from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from typing import List
from models import VehicleCount

class Database:
    def __init__(self, connection_string: str):
        self.client = AsyncIOMotorClient(connection_string)
        self.db = self.client.vehicle_counting
        self.counts = self.db.vehicle_counts

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

# Global database instance
_db = None

def get_database():
    global _db
    if _db is None:
        from config import settings
        _db = Database(settings.mongodb_url)
    return _db 