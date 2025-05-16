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
    # device_id: str
    road: str
    status: str
    timeDuration: int # thời gian đèn được chỉ định

class TrafficLightLog(TrafficLight):
    timeRemaning: int
    timestamp: datetime # thời gian còn lại của đèn cho đến khi đổi sang đèn khác


from pydantic import BaseModel, Field
from typing import Optional
from bson import ObjectId
from datetime import datetime

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class Road(BaseModel):
    id: Optional[str] = Field(alias="id", default=None)
    name: str
    location: str
    district: str
    city: str
    status: str = "Active"  # Active or Inactive
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "name": "Nguyen Van Linh",
                "location": "District 7",
                "district": "District 7",
                "city": "Ho Chi Minh City",
                "status": "Active"
            }
        }

class Device(BaseModel):
    id: Optional[str] = Field(alias="id", default=None)
    name: str
    device_id: str
    road_id: str
    type: str  # camera or traffic_light
    status: str = "Active"  # Active or Inactive
    ip_address: Optional[str] = None
    location_details: Optional[str] = None
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "name": "Camera 1",
                "device_id": "CAM-001",
                "road_id": "60d21b4667d0d61f8ab14262",  # Example ObjectId
                "type": "camera",
                "status": "Active",
                "ip_address": "192.168.1.100",
                "location_details": "North Intersection"
            }
        }

# class VehicleCount(BaseModel):
#     id: Optional[str] = Field(alias="id", default=None)
#     device_id: str
#     road_id: str
#     timestamp: datetime
#     vehicle_type: str
#     count: int
    
#     class Config:
#         allow_population_by_field_name = True
#         arbitrary_types_allowed = True
#         json_encoders = {ObjectId: str}

# class TrafficLight(BaseModel):
#     id: Optional[str] = Field(alias="id", default=None)
#     device_id: str
#     road_id: str
#     color: str  # red, yellow, green
#     status: str  # on or off
#     road: str
#     timeDuration: int  # in seconds
    
#     class Config:
#         allow_population_by_field_name = True
#         arbitrary_types_allowed = True
#         json_encoders = {ObjectId: str}

# class TrafficLightLog(BaseModel):
#     id: Optional[str] = Field(alias="id", default=None)
#     device_id: str
#     color: str  # red, yellow, green
#     changed_at: datetime
    
#     class Config:
#         allow_population_by_field_name = True
#         arbitrary_types_allowed = True
#         json_encoders = {ObjectId: str}