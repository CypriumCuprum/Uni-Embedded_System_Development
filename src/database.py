from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from typing import List
from models import VehicleCount, TrafficLight, TrafficLightLog

class Database:
    def __init__(self, connection_string: str):
        self.client = AsyncIOMotorClient(connection_string)
        self.db = self.client.vehicle_counting
        self.counts = self.db.vehicle_counts
        self.traffic_light = self.db.traffic_light
        self.traffic_light_log = self.db.traffic_light_log
    async def save_vehicle_count(self, count: VehicleCount):
        await self.counts.insert_one(count.dict())

    async def get_vehicle_counts(self, limit: int = 100) -> List[VehicleCount]:
        cursor = self.counts.find().sort("timestamp", -1).limit(limit)
        counts = await cursor.to_list(length=limit)
        return [VehicleCount(**count) for count in counts]

    async def get_counts_by_time_range(self, start_time: datetime, end_time: datetime) -> List[VehicleCount]:
        cursor = self.counts.find({
            "timestamp": {
                "$gte": start_time,
                "$lte": end_time
            }
        }).sort("timestamp", -1)
        counts = await cursor.to_list(length=None)
        return [VehicleCount(**count) for count in counts]

    async def save_traffic_light_status(self, status: TrafficLight):
        await self.traffic_light.insert_one(status.dict())
 
    async def save_traffic_light_log(self, status: TrafficLightLog):
        await self.traffic_light_log.insert_one(status.dict())

    async def get_latest_traffic_light_log(self, light_color: str) -> TrafficLightLog | None:
        doc = await self.traffic_light_log.find_one(
            {"color": light_color},
            sort=[("timestamp", -1)]
        )
        if doc:
            doc.pop("_id", None)
        return TrafficLightLog(**doc) if doc else None

    async def get_traffic_light_status(self, light_color: str, road: str) -> TrafficLight | None:
        doc = await self.traffic_light.find_one(
            {"color": light_color, "road": road}
        )
        if doc:
            doc.pop("_id", None)
        print(doc)
        return TrafficLight(**doc) if doc else None
    
    async def update_traffic_light_status(self, color: str, new_status: str, new_time_duration: int, road: str) -> bool:
        result = await self.traffic_light.update_one(
            {"color": color, "road": road},
            {"$set": {"status": new_status, "timeDuration": new_time_duration}}
        )
        return result.modified_count > 0

# Global database instance
_db = None

def get_database():
    global _db
    if _db is None:
        from config import settings
        _db = Database(settings.mongodb_url)
    return _db 