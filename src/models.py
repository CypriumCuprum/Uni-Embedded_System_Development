from pydantic import BaseModel
from typing import List, Tuple
from datetime import datetime

class Point(BaseModel):
    x: float
    y: float

class Line(BaseModel):
    start: Point
    end: Point

class AreaConfig(BaseModel):
    boundary_lines: List[Line]

class CountingLineConfig(BaseModel):
    counting_line: Line
    direction: str  # "up" or "down"

class VehicleCount(BaseModel):
    count: int
    timestamp: datetime
    vehicle_type: str
    direction: str

class StreamConfig(BaseModel):
    url: str
    fps: int = 30
    resolution: Tuple[int, int] = (640, 480) 

class TrafficLight(BaseModel):
    color: str
    road: str
    timeDuration: int
    timestamp: datetime
