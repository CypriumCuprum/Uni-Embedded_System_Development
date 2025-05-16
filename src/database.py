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
        self.roads = self.db.roads
        self.devices = self.db.devices
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
    
    async def get_total_flow_time_from_to(self, start_time: datetime, end_time: datetime):
        cursor = self.counts.find({
            "timestamp": {
                "$gte": start_time,
                "$lte": end_time
            },
            "vehicle_type": "all_down"
        }). sort("timestamp",-1)

        counts = await cursor.to_list(length=None)
        counts_start = counts[0].count
        counts_end = counts[-1].cout
        return counts_end - counts_start


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
    
    async def get_traffic_light_by_device_id(self, road: str) -> TrafficLight | None:
        doc = await self.traffic_light.find_one(
            {"road": road}
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
    async def update_device_status(self, device_id, new_status) -> bool:
        result = await self.devices.update_one( 
            { "device_id": device_id},
            {"$set": {"status": new_status}}
        )
        return result.modified_count > 0
# Road operations
    async def get_all_roads(self) -> List[dict]:
        cursor = self.roads.find()
        roads = await cursor.to_list(length=100)
        for road in roads:
            road["id"] = str(road["_id"])
        return roads
    
    async def get_road_by_id(self, road_id: str) -> dict:
        from bson import ObjectId
        road = await self.roads.find_one({"_id": ObjectId(road_id)})
        if road:
            road["id"] = str(road["_id"])
        return road
    
    async def create_road(self, road_data: dict) -> dict:
        result = await self.roads.insert_one(road_data)
        new_road = await self.roads.find_one({"_id": result.inserted_id})
        new_road["id"] = str(new_road["_id"])
        return new_road
    
    async def update_road(self, road_id: str, road_data: dict) -> dict:
        from bson import ObjectId
        result = await self.roads.update_one(
            {"_id": ObjectId(road_id)},
            {"$set": road_data}
        )
        if result.modified_count:
            updated_road = await self.roads.find_one({"_id": ObjectId(road_id)})
            updated_road["id"] = str(updated_road["_id"])
            return updated_road
        return None
    
    async def delete_road(self, road_id: str) -> bool:
        from bson import ObjectId
        result = await self.roads.delete_one({"_id": ObjectId(road_id)})
        return result.deleted_count > 0
    
    # Device operations
    async def get_all_devices(self) -> List[dict]:
        cursor = self.devices.find()
        devices = await cursor.to_list(length=100)
        for device in devices:
            device["id"] = str(device["_id"])
        return devices
    
    async def get_device_by_id(self, device_id: str) -> dict:
        from bson import ObjectId
        device = await self.devices.find_one({"_id": ObjectId(device_id)})
        if device:
            device["id"] = str(device["_id"])
        return device
    
    async def create_device(self, device_data: dict) -> dict:
        result = await self.devices.insert_one(device_data)
        new_device = await self.devices.find_one({"_id": result.inserted_id})
        new_device["id"] = str(new_device["_id"])
        print(new_device)
        if(new_device['type'] == "traffic_light"):
            print("check type: " + new_device['type'] + " " + new_device['device_id'])
            existing_traffic_light = await self.get_traffic_light_by_device_id(new_device["device_id"])

            if existing_traffic_light is None:
                print("check exist: ")
                for c in ["RED", "YELLOW", "GREEN"]:
                    trafficLight = TrafficLight(
                        color=c,
                        road=new_device["device_id"],
                        status="OFF",
                        timeDuration=int(10)
                    )
                    await self.save_traffic_light_status(trafficLight)
        return new_device
    
    async def update_device(self, device_id: str, device_data: dict) -> dict:
        from bson import ObjectId
        result = await self.devices.update_one(
            {"_id": ObjectId(device_id)},
            {"$set": device_data}
        )
        if result.modified_count:
            updated_device = await self.devices.find_one({"_id": ObjectId(device_id)})
            updated_device["id"] = str(updated_device["_id"])
            return updated_device
        return None
    
    async def delete_device(self, device_id: str) -> bool:
        from bson import ObjectId
        result = await self.devices.delete_one({"_id": ObjectId(device_id)})
        return result.deleted_count > 0

# Global database instance
_db = None

def get_database():
    global _db
    if _db is None:
        from config import settings
        _db = Database(settings.mongodb_url)
    return _db 