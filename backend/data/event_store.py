from typing import List, Dict, Any
from collections import deque

class EventStore:
    def __init__(self, max_len=10000):
        self.events = deque(maxlen=max_len)
        self.total_events = 0

    def add_event(self, event: Dict[str, Any]):
        self.events.append(event)
        self.total_events += 1

    def get_recent(self, limit: int = 100) -> List[Dict[str, Any]]:
        return list(self.events)[-limit:]

event_store = EventStore()
