from fastapi import Depends, FastAPI, WebSocket, HTTPException, Body, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse
from typing import List, Dict, Tuple
import uvicorn
from config import settings
from database import Database, get_database
from models import RoadResponse, VehicleCount, AreaConfig, CountingLineConfig
from models import CreateCameraRequest
from video_processor_v2 import VideoProcessor
from websocket_manager import WebSocketManager
import asyncio
import os
from pydantic import BaseModel
from mqtt_client import MQTTClient
from light_controller import Light_Controller
from pydantic import BaseModel, Field
from typing import List, Optional
from bson import ObjectId
from datetime import datetime
import config
from models import Road, Device, PyObjectId
from utility import RoadManager
from fastapi.logger import logger
# Get the base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="Vehicle Counting System")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define ports for each processor
PORT1 = 8080  # Main application port

# Initialize components
line_start = (0, settings.frame_height2*4//5)  # Start from left side
line_end = (settings.frame_width, settings.frame_height2*4//5)  # End at right side
loop = asyncio.get_event_loop()
mqtt_websocket_manager = WebSocketManager()
mqtt_client = MQTTClient(loop,mqtt_websocket_manager)

light_controller = Light_Controller(mqtt=mqtt_client, is_auto=False)

road_manager = RoadManager(get_database())

# Create a class manager for the video processors
class VideoProcessorManager:
    def __init__(self):
        self.processors: Dict[str, VideoProcessor] = {}

    def add_processor(self, device: Device):
        # check if processor_name already exists
        processor_id = device.device_id
        if processor_id in self.processors:
            return {"status": "error", "message": f"Processor {processor_id} already exists."}
        self.processors[processor_id] = VideoProcessor(
            device_id=processor_id,
            input_video_stream=device.ip_address,
            direction_from=device.direction_from,
            direction_to=device.direction_to,
        )
        return {"status": "success", "message": f"Processor {processor_id} added."}

    def get_processor(self, processor_id: str) -> VideoProcessor:
        return self.processors.get(processor_id)

    def remove_processor(self, processor_id: str):
        if processor_id in self.processors:
            del self.processors[processor_id]
            return {"status": "success", "message": f"Processor {processor_id} removed."}
        return {"status": "error", "message": f"Processor {processor_id} not found."}

video_processor_manager = VideoProcessorManager()

@app.on_event("startup")
async def startup_event():
    try:
        mqtt_client.connect()
    except:
        print("MQTT connection failed. Please check your broker settings.")
    # mqtt_client.publish(settings.mqtt_topic_pub, "30000;5000;20000")
    cameras_from_database = await get_database().get_all_cameras()
    cnt = 0
    for camera in cameras_from_database:
        camera = Device(**camera)
        video_processor_manager.add_processor(camera)
        if camera.status == "Active":
            try:
                if cnt == 0:
                    video_processor_manager.processors[camera.device_id].is_tracking = True
                    cnt += 1
                video_processor_manager.processors[camera.device_id].set_counting_line(line_start, line_end)
                await video_processor_manager.processors[camera.device_id].start_stream()
            except Exception as e:
                print(f"Error starting stream for camera {camera.device_id}: {e}")
    try:
        await road_manager.initialize_roads()
    except Exception as e:
        print(f"Error initializing roads: {e}")


@app.post("/roads/{road_id}/auto", summary="Kích hoạt chế độ tự động cho nút giao")
async def set_road_auto_control(road_id: str):
    try:
        await road_manager.invoke_auto_control(road_id)
        return {"message": f"Auto control successfully invoked for road ID {road_id}."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"API Error on /roads/{road_id}/auto: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal server error occurred.")


@app.post("/roads/{road_id}/manual", summary="Kích hoạt chế độ thủ công cho nút giao")
async def set_road_manual_control(road_id: str):
    try:
        await road_manager.invoke_manual_control(road_id)
        return {"message": f"Manual control successfully invoked for road ID {road_id}."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"API Error on /roads/{road_id}/manual: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal server error occurred.")

# Database dependency
async def get_db():
    return get_database()

# Define request models
class CountingLineRequest(BaseModel):
    start: List[int]
    end: List[int]
    processor_id: int = 1  # Default to first processor


# Thêm nhưng chưa biết dùng làm gì
@app.post("/turn_on_camera")
async def turn_on_camera(device_id: str):
    """Turn on camera and start processing"""
    try:
        video_processor_manager.processors[device_id].set_counting_line(line_start, line_end)
        await video_processor_manager.processors[device_id].start_stream()

        return {"status": "success", "message": f"Camera {device_id} turned on and processing started."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Thêm nhưng chưa biết dùng làm gì
@app.post("/turn_off_camera")
async def turn_off_camera(device_id: str):
    """Turn off camera and stop processing"""
    try:
        video_processor_manager.processors[device_id].stop()

        return {"status": "success", "message": f"Camera {device_id} turned off and processing stopped."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# @app.get("/{device_id}/stream.mjpg")
# async def video_stream2(device_id: str):
#     """Stream the second processed video feed"""
#     return StreamingResponse(
#         video_processor_manager.processors[device_id].generate_frames(),
#         media_type="multipart/x-mixed-replace; boundary=boundary"
#     )

# endpoint to change traffic cycles
@app.post("/api/cycle")
async def change_cycle(message: str):
    greenTime1, redTime1 = map(int, message.split(","))
    yellowTime1 = 3
    redTime2 = greenTime1 + yellowTime1
    yellowTime2 = 3
    greenTime2 = redTime1 - yellowTime1
    message1 = f"1,{greenTime1*1000},{yellowTime1*1000},{redTime1*1000}"
    message2 = f"2,{greenTime2*1000},{yellowTime2*1000},{redTime2*1000}"
    mqtt_client.publish(settings.mqtt_topic_pub, message1)
    mqtt_client.publish(settings.mqtt_topic_pub, message2)
    return {f"message_pub to {settings.mqtt_topic_pub}"}


# WebSocket endpoint for MQTT data
@app.websocket("/ws/mqtt1")
async def websocket_mqtt_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time MQTT updates"""
    await websocket.accept()  # Sử dụng accept trực tiếp vì chưa có phương thức connect trong code bạn chia sẻ
    client_host = websocket.client.host
    client_port = websocket.client.port
    print(f"MQTT WebSocket connection accepted from: {client_host}:{client_port}")
    # Thêm websocket vào danh sách kết nối của mqtt_websocket_manager
    if not hasattr(mqtt_websocket_manager, "active_connections"):
        mqtt_websocket_manager.active_connections = []
    mqtt_websocket_manager.active_connections.append(websocket)
    mqtt_websocket_manager.list_channel["mqtt1"] = websocket
    
    try:
        # Gửi thông báo kết nối thành công
        await websocket.send_json({
            "type": "mqtt_connection",
            "status": "connected",
            "message": "Connected to MQTT WebSocket endpoint"
        })
        
        # Giữ kết nối mở
        while True:
            # Chờ tin nhắn từ client (nếu cần)
            data = await websocket.receive_text()
            # Xử lý tin nhắn từ client nếu cần
            print(f"Received message from MQTT WebSocket client")
    except WebSocketDisconnect:
        print(f"Client disconnected from MQTT websocket: {client_host}:{client_port}")
        # Xóa websocket khỏi danh sách kết nối
        if websocket in mqtt_websocket_manager.active_connections:
            mqtt_websocket_manager.active_connections.remove(websocket)
    except Exception as e:
        print(f"MQTT WebSocket error: {e}")
        # Xóa websocket khỏi danh sách kết nối trong trường hợp lỗi
        if hasattr(mqtt_websocket_manager, "active_connections"):
            if websocket in mqtt_websocket_manager.active_connections:
                mqtt_websocket_manager.active_connections.remove(websocket)
                mqtt_websocket_manager.list_channel.pop("mqtt1")

# WebSocket endpoint for MQTT data
@app.websocket("/ws/mqtt2")
async def websocket_mqtt_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time MQTT updates"""
    await websocket.accept()  # Sử dụng accept trực tiếp vì chưa có phương thức connect trong code bạn chia sẻ
    client_host = websocket.client.host
    client_port = websocket.client.port
    print(f"MQTT WebSocket connection accepted from: {client_host}:{client_port}")
    
    # Thêm websocket vào danh sách kết nối của mqtt_websocket_manager
    if not hasattr(mqtt_websocket_manager, "active_connections"):
        mqtt_websocket_manager.active_connections = []
    mqtt_websocket_manager.active_connections.append(websocket)
    mqtt_websocket_manager.list_channel["mqtt2"] = websocket
    try:
        # Gửi thông báo kết nối thành công
        await websocket.send_json({
            "type": "mqtt_connection",
            "status": "connected",
            "message": "Connected to MQTT WebSocket endpoint"
        })
        
        # Giữ kết nối mở
        while True:
            # Chờ tin nhắn từ client (nếu cần)
            data = await websocket.receive_text()
            # Xử lý tin nhắn từ client nếu cần
            print(f"Received message from MQTT WebSocket client")
    except WebSocketDisconnect:
        print(f"Client disconnected from MQTT websocket: {client_host}:{client_port}")
        # Xóa websocket khỏi danh sách kết nối
        if websocket in mqtt_websocket_manager.active_connections:
            mqtt_websocket_manager.active_connections.remove(websocket)
    except Exception as e:
        print(f"MQTT WebSocket error: {e}")
        # Xóa websocket khỏi danh sách kết nối trong trường hợp lỗi
        if hasattr(mqtt_websocket_manager, "active_connections"):
            if websocket in mqtt_websocket_manager.active_connections:
                mqtt_websocket_manager.active_connections.remove(websocket)
                mqtt_websocket_manager.list_channel.pop("mqtt2")

# ========== Road Endpoints ==========

@app.get("/api/roads/device/all", response_model=List[RoadResponse])
async def list_roads(db: Database = Depends(get_db)):
    roads = await db.get_all_roads_and_devices()
    return roads

@app.get("/api/roads", response_model=List[Road])
async def list_roads(db: Database = Depends(get_db)):
    roads = await db.get_all_roads()
    return roads

@app.post("/api/roads", response_model=Road)
async def create_road(road: Road, db: Database = Depends(get_db)):
    road_dict = road.dict(exclude={"id"})
    # Remove any None values for MongoDB
    road_dict = {k: v for k, v in road_dict.items() if v is not None}
    
    # Create the road
    created_road = await db.create_road(road_dict)
    return created_road

@app.get("/api/roads/{road_id}", response_model=Road)
async def get_road(road_id: str, db: Database = Depends(get_db)):
    road = await db.get_road_by_id(road_id)
    if not road:
        raise HTTPException(status_code=404, detail="Road not found")
    return road

@app.put("/api/roads/{road_id}", response_model=Road)
async def update_road(road_id: str, road: Road, db: Database = Depends(get_db)):
    # Check if road exists
    existing_road = await db.get_road_by_id(road_id)
    if not existing_road:
        raise HTTPException(status_code=404, detail="Road not found")
    
    # Prepare data for update
    road_dict = road.dict(exclude={"id"})
    road_dict = {k: v for k, v in road_dict.items() if v is not None}
    
    # Update the road
    updated_road = await db.update_road(road_id, road_dict)
    if not updated_road:
        raise HTTPException(status_code=500, detail="Failed to update road")
    return updated_road

@app.delete("/api/roads/{road_id}")
async def delete_road(road_id: str, db: Database = Depends(get_db)):
    # Check if road exists
    existing_road = await db.get_road_by_id(road_id)
    if not existing_road:
        raise HTTPException(status_code=404, detail="Road not found")
    
    # Delete the road
    success = await db.delete_road(road_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete road")
    return {"message": "Road successfully deleted"}

# ========== Device Endpoints ==========

@app.get("/api/devices", response_model=List[Device])
async def list_devices(db: Database = Depends(get_db)):
    devices = await db.get_all_devices()
    return devices

@app.post("/api/devices", response_model=Device)
async def create_device(device: Device, db: Database = Depends(get_db)):
    # Check if road exists
    try:
        road = await db.get_road_by_id(device.road_id)
        if not road:
            raise HTTPException(status_code=404, detail=f"Road with ID {device.road_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking road: {str(e)}")

    if device.type == "camera":
        # Check if device is already added to the video processor manager
        if device.device_id in video_processor_manager.processors:
            raise HTTPException(status_code=400, detail="Device is already added to the video processor manager")
        try:
            video_processor_manager.add_processor(device)
            if device.status == "Active":
                await video_processor_manager.processors[device.device_id].start_stream()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to add video processor: {str(e)}")
    
    device_dict = device.dict(exclude={"id"})
    # Remove any None values for MongoDB
    device_dict = {k: v for k, v in device_dict.items() if v is not None}
    
    # Create the device
    created_device = await db.create_device(device_dict)
    return created_device

@app.get("/api/devices/{device_id}", response_model=Device)
async def get_device(device_id: str, db: Database = Depends(get_db)):
    device = await db.get_device_by_id(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device

@app.put("/api/devices/{device_id}", response_model=Device)
async def update_device(device_id: str, device: Device, db: Database = Depends(get_db)):
    # Check if device exists
    existing_device = await db.get_device_by_id(device_id)
    if not existing_device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Check if road exists
    road = await db.get_road_by_id(device.road_id)
    if not road:
        raise HTTPException(status_code=404, detail=f"Road with ID {device.road_id} not found")
    
    # Prepare data for update
    device_dict = device.dict(exclude={"id"})
    device_dict = {k: v for k, v in device_dict.items() if v is not None}
    
    # Update the device
    updated_device = await db.update_device(device_id, device_dict)
    if not updated_device:
        raise HTTPException(status_code=500, detail="Failed to update device")
    return updated_device

@app.delete("/api/devices/{device_id}")
async def delete_device(device_id: str, db: Database = Depends(get_db)):
    # Check if device exists
    existing_device = await db.get_device_by_id(device_id)
    if not existing_device:
        raise HTTPException(status_code=404, detail="Device not found")

    if existing_device["type"] == "camera":
        # Check if device is in the video processor manager
        if device_id in video_processor_manager.processors:
            # Stop the video processor
            video_processor_manager.processors[device_id].stop()
            # Remove the processor from the manager
            video_processor_manager.remove_processor(device_id)
    
    # Delete the device
    success = await db.delete_device(device_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete device")
    return {"message": "Device successfully deleted"}

@app.get("/api/devices/{road_id}", response_model=List[Device])
async def get_devices_by_road(road_id: str, db: Database = Depends(get_db)):
    devices = await db.get_device_by_road_id(road_id)
    if not devices:
        raise HTTPException(status_code=404, detail="Devices not found for this road")
    return devices

# ============ Video Streaming Endpoints for each Camera ==========
@app.get("/api/devices/{device_id}/stream.mjpg")
async def video_stream(device_id: str):
    """Stream the processed video feed"""
    processor = video_processor_manager.get_processor(device_id)
    if not processor:
        raise HTTPException(status_code=404, detail="Processor not found")

    return StreamingResponse(
        processor.generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=boundary"
    )

if __name__ == "__main__":
    # Ensure we're in the correct directory
    os.chdir(BASE_DIR)
    # We'll run the application on PORT1, and each video processor will expose its stream on its own port
    uvicorn.run("main2:app", host="0.0.0.0", port=PORT1, reload=True)