from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv
import socket

load_dotenv()

class Settings(BaseSettings):

    def get_local_ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        finally:
            s.close()
        return ip

    # MongoDB settings
    mongodb_url: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    
    # YOLOv8 settings
    model_path: str = os.getenv("YOLO_MODEL_PATH", "yolov8n.pt")
    conf_thresh: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))
    iou_thresh: float = float(os.getenv("IOU_THRESHOLD", "0.7"))  # Ngưỡng IOU cho NMS

    # Video processing settings
    frame_width: int = int(os.getenv("FRAME_WIDTH", "640"))
    frame_height: int = int(os.getenv("FRAME_HEIGHT", "480"))
    frame_width2: int = int(os.getenv("FRAME_WIDTH2", "480"))
    frame_height2: int = int(os.getenv("FRAME_HEIGHT2", "640"))
    fps: int = int(os.getenv("FPS", "30"))
    video_url: str = os.getenv("VIDEO_URL", "C:\\Users\\PC\\Documents\\Y4\\T8\\Embedding\\src\\Uni-Embedded_System_Development\\video\\vehicles.mp4")
    # ByteTrack settings
    track_thresh: float = float(os.getenv("TRACK_THRESH", "0.5"))  # Detection confidence threshold
    track_buffer: int = int(os.getenv("TRACK_BUFFER", "30"))      # Maximum number of frames to keep lost tracks
    match_thresh: float = float(os.getenv("MATCH_THRESH", "0.8")) # IOU threshold for matching detections to tracks
    
    # API settings
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    
    # MQTT 
    mqtt_broker: str = os.getenv("MQTT_BROKER", str(get_local_ip()))
    mqtt_port: int = int(os.getenv("MQTT_PORT", "1883"))
    mqtt_topic_pub: str = os.getenv("MQTT_TOPIC_PUB", "traffic_lights/cycles")
    mqtt_topic_sub: str = os.getenv("MQTT_TOPIC_SUB", "traffic_lights/noti")

    class Config:
        env_file = ".env"
        protected_namespaces = ("settings_",)

settings = Settings() 