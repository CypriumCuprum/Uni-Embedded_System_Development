from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # MongoDB settings
    mongodb_url: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    
    # YOLOv8 settings
    model_path: str = os.getenv("YOLO_MODEL_PATH", "yolov8n.pt")
    conf_thresh: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))
    iou_thresh: float = float(os.getenv("IOU_THRESHOLD", "0.7"))  # Ngưỡng IOU cho NMS

    # Video processing settings
    frame_width: int = int(os.getenv("FRAME_WIDTH", "640"))
    frame_height: int = int(os.getenv("FRAME_HEIGHT", "480"))
    fps: int = int(os.getenv("FPS", "30"))
    
    # ByteTrack settings
    track_thresh: float = float(os.getenv("TRACK_THRESH", "0.5"))  # Detection confidence threshold
    track_buffer: int = int(os.getenv("TRACK_BUFFER", "30"))      # Maximum number of frames to keep lost tracks
    match_thresh: float = float(os.getenv("MATCH_THRESH", "0.8")) # IOU threshold for matching detections to tracks
    
    # API settings
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    
    class Config:
        env_file = ".env"

settings = Settings() 