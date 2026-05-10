import asyncio
import json
from typing import List, Dict, Any
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

    async def broadcast_event(self, event: Dict[str, Any]):
        await self.broadcast(json.dumps({"type": "threat_event", "event": event}))

    async def broadcast_stats(self, stats: Dict[str, Any]):
        await self.broadcast(json.dumps({"type": "stats_update", "stats": stats}))


manager = ConnectionManager()
