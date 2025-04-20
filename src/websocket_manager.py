from fastapi import WebSocket
from typing import List, Dict
import json

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.list_channel: Dict[str, WebSocket] = {}
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to client: {e}")
                await self.disconnect(connection)

    async def broadcastMQTT(self, channel: str, message: Dict):
        webSocket = self.list_channel[channel]
        print(webSocket)
        try:
            await webSocket.send_json(message)
        except Exception as e:
            print(f"Error broadcasting to client: {e}")
            await self.disconnect(webSocket)

    async def broadcast_count_update(self, count: int, vehicle_type: str, direction: str):
        message = {
            "type": "count_update",
            "data": {
                "count": count,
                "vehicle_type": vehicle_type,
                "direction": direction
            }
        }
        await self.broadcast(message) 