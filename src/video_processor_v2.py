import cv2
import numpy as np
from ultralytics import YOLO
import supervision as sv
import time
from typing import Optional, Tuple, List, Dict, Set
import asyncio
from datetime import datetime
import json
import os
from config import settings
from database import get_database
from models import VehicleCount, AggregatedVehicleCount
import torch

class VideoProcessor:
    def __init__(self,device_id, input_video_stream, direction_from, direction_to, is_tracking=False, stream_port: int = 8081):
        """Initialize the video processor with YOLO model and ByteTrack"""
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(self.base_dir, 'yolov8n.pt')
        self.model = YOLO(model_path)
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model.to(device)

        # --- Class Information ---
        self.class_names = dict(self.model.names)
        self.vehicle_class_ids = {
            k for k, v in self.class_names.items()
            if v in ['car', 'motorcycle', 'bus', 'truck', 'bicycle'] # Thêm 'bicycle' nếu cần
        }
        print(f"Vehicle class IDs being tracked: {self.vehicle_class_ids}")
        print(f"Class names: {self.class_names}")


        self.tracker = sv.ByteTrack(
            track_activation_threshold=settings.track_thresh,
            lost_track_buffer=settings.track_buffer,
            minimum_matching_threshold=settings.match_thresh,
            frame_rate=settings.fps,
            minimum_consecutive_frames=3
        )
        self.box_annotator = sv.BoxAnnotator(thickness=2) # Giảm độ dày viền
        self.label_annotator = sv.LabelAnnotator(text_thickness=1, text_scale=0.7, text_color=sv.Color.BLACK) # Giảm kích thước text
        self.trace_annotator = sv.TraceAnnotator(thickness=2, trace_length=30) # Giảm độ dày và độ dài trace

        self.line_zone: Optional[sv.LineZone] = None
        self.line_zone_annotator: Optional[sv.LineZoneAnnotator] = None
        self.line_y: Optional[int] = None # Lưu tọa độ y của vạch đếm (giả sử là ngang)

        self.frame_count = 0
        self.start_time = None
        self.fps = 0
        self.counts_all = 0

        # --- Cấu trúc đếm mới ---
        self.counts: Dict[str, any] = {
            'total_down': 0,
            'down_by_class': {self.class_names[cls_id]: 0 for cls_id in self.vehicle_class_ids if cls_id in self.class_names},
            'fps': 0.0 # Thêm FPS vào đây để gửi qua WebSocket
        }
        self.crossed_down_ids: Set[int] = set() # Set để lưu tracker_id đã đi xuống

        self.last_count_time = time.time()
        self.last_db_save_time = time.time()
        self.count_history = []
        self.count_interval = 1  # Giữ nguyên khoảng thời gian cập nhật history (tùy chọn)
        self.db_save_interval = 60  # seconds
        self.is_running = False
        self.current_frame = None
        self.frame_lock = asyncio.Lock()
        self.cap = None
        self.stream_port = stream_port
        self.stream_url = input_video_stream
        self.db = get_database()
        self.deviceid = device_id
        self.direction_from = direction_from
        self.direction_to = direction_to
        self.is_tracking = is_tracking

    def set_counting_line(self, start: Tuple[int, int], end: Tuple[int, int]):
        """Set up the counting line."""
        # Giả sử đường kẻ là ngang để đơn giản hóa việc xác định hướng đi xuống
        # Nếu đường kẻ không ngang, logic kiểm tra vượt qua cần phức tạp hơn
        if start[1] != end[1]:
            print("Warning: Counting line is not horizontal. Downward counting logic assumes a horizontal line.")
        self.line_y = start[1] # Lưu tọa độ y của đường kẻ

        self.line_zone = sv.LineZone(
            start=sv.Point(start[0], start[1]),
            end=sv.Point(end[0], end[1])
        )
        self.line_zone_annotator = sv.LineZoneAnnotator(thickness=2, text_thickness=0, text_scale=0)
        print(f"Counting line set at Y = {self.line_y}")

    def reset_counts(self):
        """Resets the counters and the set of crossed IDs."""
        print("Resetting counts...")
        self.counts = {
            'total_down': 0,
            'down_by_class': {self.class_names[cls_id]: 0 for cls_id in self.vehicle_class_ids if cls_id in self.class_names},
            'fps': self.fps # Giữ lại giá trị fps hiện tại
        }
        self.crossed_down_ids = set()
        if self.line_zone:
             start_pt = self.line_zone.vector.start
             end_pt = self.line_zone.vector.end
             self.line_zone = sv.LineZone(start=start_pt, end=end_pt)

    async def process_frame(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """Process a single frame."""
        if frame is None or self.line_y is None: # Cần có đường kẻ mới xử lý
            return None

        frame = cv2.resize(frame, (settings.frame_width2, settings.frame_height2))
        results = self.model(frame, conf=settings.conf_thresh, iou=settings.iou_thresh, classes=list(self.vehicle_class_ids), verbose=False)[0]
        detections = sv.Detections.from_ultralytics(results)

        detections = self.tracker.update_with_detections(detections)

        annotated_frame = frame.copy()

        current_crossed_ids_in_frame = set()
        if len(detections) > 0 and detections.tracker_id is not None:
            for xyxy, confidence, class_id, tracker_id in zip(detections.xyxy, detections.confidence, detections.class_id, detections.tracker_id):
                if tracker_id is None:
                    continue

                anchor_point_y = int(xyxy[3])

                if anchor_point_y > self.line_y and tracker_id not in self.crossed_down_ids:
                    if class_id in self.vehicle_class_ids and class_id in self.class_names:
                        class_name = self.class_names[class_id]
                        self.counts['down_by_class'][class_name] += 1
                        self.counts['total_down'] += 1
                        self.counts_all += 1
                        self.crossed_down_ids.add(tracker_id) # Đánh dấu ID này đã đi qua
                        current_crossed_ids_in_frame.add(tracker_id) # Đánh dấu ID vừa qua trong frame này
                        print(f"Vehicle crossed down: ID {tracker_id}, Type: {class_name}, Total Down: {self.counts['total_down']}") # Log
                    else:
                         print(f"Ignoring cross for ID {tracker_id}, Class ID {class_id} (Valid vehicles: {self.vehicle_class_ids})")
                         pass


        # --- Vẽ Annotation ---
        labels = []
        if len(detections) > 0 and detections.tracker_id is not None:
             labels = [
                 # Đánh dấu (*) nếu xe vừa vượt qua trong frame này
                 f"#{tracker_id}{'*' if tracker_id in current_crossed_ids_in_frame else ''} {self.class_names[class_id]} {confidence:0.2f}"
                 for confidence, class_id, tracker_id
                 in zip(detections.confidence, detections.class_id, detections.tracker_id) if class_id in self.class_names
             ]

        # Vẽ trace, box, label
        if len(detections)>0:
            annotated_frame = self.trace_annotator.annotate(scene=annotated_frame, detections=detections)
            annotated_frame = self.box_annotator.annotate(scene=annotated_frame, detections=detections)
            annotated_frame = self.label_annotator.annotate(scene=annotated_frame, detections=detections, labels=labels)

        # Vẽ đường kẻ (không cần hiển thị số đếm của LineZone nữa)
        if self.line_zone_annotator:
            annotated_frame = self.line_zone_annotator.annotate(annotated_frame, line_counter=self.line_zone) # Vẫn cần line_zone object

        # Tính FPS
        current_time_fps = time.time()
        if self.start_time is None:
            self.start_time = current_time_fps
        else:
            self.frame_count += 1
            elapsed_time = current_time_fps - self.start_time
            if elapsed_time >= 1.0: # Cập nhật FPS mỗi giây
                self.fps = self.frame_count / elapsed_time
                self.counts['fps'] = round(self.fps, 1) # Cập nhật FPS vào dict counts
                self.frame_count = 0
                self.start_time = current_time_fps

        # --- Hiển thị thông tin đếm mới ---
        cv2.putText(annotated_frame, f"FPS: {self.fps:.1f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(annotated_frame, f"Total Down: {self.counts['total_down']}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        # Hiển thị số đếm từng loại
        start_y = 90
        for i, (class_name, count) in enumerate(self.counts['down_by_class'].items()):
             text = f"- {class_name}: {count}"
             cv2.putText(annotated_frame, text, (15, start_y + i * 25),
                         cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)


        current_time_db = time.time()

        # Lưu vào DB
        if current_time_db - self.last_db_save_time >= self.db_save_interval:
            await self._save_to_database(datetime.fromtimestamp(current_time_db))
            self.last_db_save_time = current_time_db

        return annotated_frame

    async def _save_to_database(self, current_time: datetime):
        """Save current aggregated counts to database."""
        data_to_save = AggregatedVehicleCount(
            deviceID=self.deviceid,
            timefrom=datetime.fromtimestamp(self.last_count_time),
            timeto=current_time,
            direction_from=self.direction_from,
            direction_to=self.direction_to,# Giả sử chỉ có hướng "down" từ code hiện tại
            totalCount=self.counts.get('total_down', 0), # Sử dụng alias
            countsByClass=self.counts.get('down_by_class', {}), # Sử dụng alias
            fps=self.counts.get('fps', 0.0)
        )

        try:
            await self.db.save_aggregated_vehicle_count(data_to_save)
            self.reset_counts()
            print(f"Successfully saved aggregated count record to database for device {self.deviceid}.")

        except Exception as e:
            print(f"Error saving aggregated count to database for device {self.deviceid}: {e}")

    async def start_stream(self):
        """Start processing video stream"""

        try:
            # Reset counts khi bắt đầu stream mới
            self.reset_counts()
            # Đảm bảo line_y đã được thiết lập trước khi bắt đầu
            if self.line_y is None:
                 print("Warning: Counting line not set before starting stream. Using default.")
                 # Thiết lập một đường kẻ mặc định nếu chưa có
                 default_start = (0, settings.frame_height // 2)
                 default_end = (settings.frame_width, settings.frame_height // 2)
                 self.set_counting_line(default_start, default_end)


            self.cap = cv2.VideoCapture(self.stream_url)
            if not self.cap.isOpened():
                raise Exception(f"Could not open video stream: {self.stream_url}")

            self.is_running = True
            print(f"Started processing stream: {self.stream_url}")
            asyncio.create_task(self._process_stream())

        except Exception as e:
            print(f"Error starting stream: {e}")
            self.stop() # Dừng hẳn nếu có lỗi khi khởi tạo
            raise

    async def _process_stream(self):
        """Process video stream in background with auto-restart"""
        last_error_time = 0
        error_throttle_period = 5 # seconds
        reopen_attempts = 0
        max_reopen_attempts = 5

        while self.is_running:
            try:
                if self.cap is None or not self.cap.isOpened():
                    current_time = time.time()
                    if current_time - last_error_time < error_throttle_period:
                        await asyncio.sleep(1) # Tránh spam lỗi liên tục
                        continue

                    last_error_time = current_time
                    stream_url = getattr(self, 'stream_url', None)
                    if stream_url and reopen_attempts < max_reopen_attempts:
                        reopen_attempts += 1
                        print(f"Attempting to reopen stream ({reopen_attempts}/{max_reopen_attempts}): {stream_url}")
                        self.cap = cv2.VideoCapture(stream_url)
                        if not self.cap.isOpened():
                            print(f"Failed to reopen stream attempt {reopen_attempts}.")
                            self.cap = None # Đảm bảo cap là None nếu không mở được
                            await asyncio.sleep(3)
                            continue
                        else:
                            print(f"Successfully reopened video stream: {stream_url}")
                            reopen_attempts = 0 # Reset số lần thử khi thành công
                    elif not stream_url:
                         print("Stream URL not set. Cannot process.")
                         await asyncio.sleep(5)
                         continue
                    else: # Đã thử quá nhiều lần
                        print(f"Max reopen attempts reached for {stream_url}. Stopping processing.")
                        self.is_running = False # Dừng hẳn nếu không thể mở lại stream
                        break # Thoát vòng lặp

                # --- Đọc frame ---
                ret, frame = self.cap.read()

                if not ret:
                    print("End of stream or cannot read frame. Checking stream type...")
                    is_file = not (self.stream_url and (self.stream_url.startswith(('http://', 'https://', 'rtsp://')) or self.stream_url.isdigit()))

                    if is_file:
                        print("End of video file reached. Resetting to beginning.")
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        await asyncio.sleep(0.1) # Chờ chút trước khi đọc lại
                        continue
                    else:
                        print("Stream ended or connection lost. Attempting to reopen...")
                        if self.cap:
                            self.cap.release()
                        self.cap = None # Đặt là None để logic ở đầu vòng lặp thử mở lại
                        reopen_attempts = 0 # Reset để bắt đầu thử lại từ đầu
                        await asyncio.sleep(2) # Chờ trước khi thử mở lại
                        continue

                if self.is_tracking:
                    processed_frame = await self.process_frame(frame)
                else:
                    processed_frame = frame
                    current_time_db = time.time()
                    if current_time_db - self.last_db_save_time >= self.db_save_interval:
                        await self._save_to_database(datetime.fromtimestamp(current_time_db))
                        self.last_db_save_time = current_time_db

                if processed_frame is not None:
                    async with self.frame_lock:
                        self.current_frame = processed_frame
                else:
                    pass

                await asyncio.sleep(0.01) # Delay cố định nhỏ

            except Exception as e:
                current_time = time.time()
                if current_time - last_error_time > error_throttle_period:
                     print(f"Error processing stream: {e} ({type(e).__name__})")
                     last_error_time = current_time
                await asyncio.sleep(2)

        # --- Cleanup khi vòng lặp kết thúc ---
        print("Stream processing loop finished.")
        if self.cap is not None:
            print("Releasing video capture...")
            self.cap.release()
            self.cap = None
        self.is_running = False
        print("VideoProcessor stopped.")


    async def get_frame(self) -> Optional[bytes]:
        """Get the current frame as JPEG bytes"""
        frame_to_encode = None
        async with self.frame_lock:
             if self.current_frame is not None:
                  frame_to_encode = self.current_frame.copy() # Tạo bản sao để tránh race condition

        if frame_to_encode is not None:
            try:
                ret, buffer = cv2.imencode('.jpg', frame_to_encode, [cv2.IMWRITE_JPEG_QUALITY, 85])
                if ret:
                    return buffer.tobytes()
            except Exception as e:
                 print(f"Error encoding frame: {e}")
        return None # Trả về None nếu không có frame hoặc lỗi encode


    async def generate_frames(self):
        """Generate MJPEG frames for streaming"""
        while self.is_running:
            frame_bytes = await self.get_frame()
            if frame_bytes is not None:
                try:
                    yield (b'--boundary\r\n'
                           b'Content-Type: image/jpeg\r\n'
                           b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n\r\n' +
                           frame_bytes + b'\r\n')
                except Exception as e:
                     print(f"Error yielding frame bytes: {e}")
            await asyncio.sleep(1/30)


    def stop(self):
        """Stop the video processing"""
        print("Stopping VideoProcessor...")
        self.is_running = False

    def get_counts(self) -> dict:
        """Get current counting statistics (new structure)"""
        return self.counts.copy()

    def get_count_history(self) -> List[dict]:
        """Get the history of counts (new structure)"""
        # Trả về bản sao của history
        return self.count_history[:] # Shallow copy is usually sufficient

    def get_stream_url(self) -> str:
        """Get the URL for accessing the processed video stream"""
        host = "localhost"
        return f"http://{host}:{self.stream_port}/stream.mjpg"


if __name__ == "__main__":
    # Test VideoProcessor
    image_path = "D:\CUPRUM\PTIT\Term_8\Embedded_System_Development\BE_AI\image_test\\testtyty.png"
    #
    # image = cv2.imread(image_path)
    # if image is None:
    #     print("Error: Could not read the image.")
    # else:
    #     processed_image = video_processor.detect_image(image)
    #     cv2.imshow("Processed Image", processed_image)
    #     cv2.waitKey(0)
    #     cv2.destroyAllWindows()