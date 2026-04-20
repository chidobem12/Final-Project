import asyncio
import json
import time
from collections import defaultdict, deque
from typing import List, Dict, Any
from fastapi import WebSocket

from ..incidents.models import CreateIncidentRequest
from ..incidents.store import incident_store


_source_attack_windows: dict[str, deque[float]] = defaultdict(deque)

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

    async def broadcast_incident(self, incident: Dict[str, Any]):
        await self.broadcast(json.dumps({"type": "incident_created", "incident": incident}))


def evaluate_event_for_incident(event: Dict[str, Any]) -> Dict[str, Any] | None:
    if event.get("prediction") != "ATTACK":
        return None

    source_ip = event.get("source_ip")
    event_id = event.get("event_id")
    if not source_ip or not event_id:
        return None

    now = time.time()
    one_minute_ago = now - 60
    window = _source_attack_windows[source_ip]
    window.append(now)
    while window and window[0] < one_minute_ago:
        window.popleft()

    severity = event.get("severity", "MEDIUM")
    severe_event = severity == "CRITICAL"
    burst_detected = len(window) >= 3
    if not (severe_event or burst_detected):
        return None

    open_incident = incident_store.find_open_by_source(source_ip)
    if open_incident:
        if event_id not in open_incident.event_ids:
            open_incident.event_ids.append(event_id)
            open_incident.updated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        return None

    incident_severity = "CRITICAL" if severe_event else "HIGH"
    created = incident_store.create(
        CreateIncidentRequest(
            severity=incident_severity,
            attack_type=event.get("attack_type", "Unknown"),
            source_ip=source_ip,
            event_id=event_id,
            notes="Auto-created by detection rule.",
        )
    )
    return created.model_dump()

manager = ConnectionManager()
