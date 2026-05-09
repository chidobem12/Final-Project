import asyncio
from typing import Dict, Any

from .packet_generator import generate_event
from .attack_scenarios import SCENARIOS
from ..api.ws_handler import evaluate_event_for_incident, manager
from ..ml.predictor import predictor
from ..data.event_store import event_store
from ..data.stats_aggregator import stats_aggregator

class NetworkSimulator:
    def __init__(self):
        self.running = False
        self.threat_rate = 0.05
        self.events_per_second = 10
        self.active_scenario = None
        self.scenario_end_time = 0
        self.scenario_started_at = 0
        self.scenario_events_generated = 0
        self.scenario_events_flagged = 0
        self.last_scenario_summary: Dict[str, Any] | None = None

    def start(self):
        self.running = True

    def pause(self):
        self.running = False

    def resume(self):
        self.running = True

    def trigger_scenario(self, scenario_id: str):
        if scenario_id in SCENARIOS:
            self.active_scenario = SCENARIOS[scenario_id]
            self.scenario_started_at = asyncio.get_event_loop().time()
            self.scenario_end_time = self.scenario_started_at + self.active_scenario["duration_seconds"]
            self.scenario_events_generated = 0
            self.scenario_events_flagged = 0

    def _finalize_scenario(self) -> Dict[str, Any] | None:
        if not self.active_scenario:
            return self.last_scenario_summary

        duration = max(asyncio.get_event_loop().time() - self.scenario_started_at, 0)
        detection_rate = (
            self.scenario_events_flagged / self.scenario_events_generated
            if self.scenario_events_generated > 0
            else 0.0
        )
        summary = {
            "scenario_name": self.active_scenario["name"],
            "duration_seconds": int(duration),
            "events_generated": self.scenario_events_generated,
            "events_flagged": self.scenario_events_flagged,
            "detection_rate": round(detection_rate, 3),
        }
        self.last_scenario_summary = summary
        self.active_scenario = None
        self.scenario_end_time = 0
        self.scenario_started_at = 0
        self.scenario_events_generated = 0
        self.scenario_events_flagged = 0
        return summary

    def stop_scenario(self) -> Dict[str, Any]:
        if self.active_scenario:
            summary = self._finalize_scenario()
            return summary or {
                "scenario_name": "Unknown",
                "duration_seconds": 0,
                "events_generated": 0,
                "events_flagged": 0,
                "detection_rate": 0.0,
            }

        return self.last_scenario_summary or {
            "scenario_name": "No active scenario",
            "duration_seconds": 0,
            "events_generated": 0,
            "events_flagged": 0,
            "detection_rate": 0.0,
        }

    async def run(self):
        self.start()
        while True:
            if not self.running:
                await asyncio.sleep(1)
                continue

            current_time = asyncio.get_event_loop().time()
            if self.active_scenario and current_time > self.scenario_end_time:
                self._finalize_scenario()

            # Calculate current batch size
            eps = self.active_scenario["events_per_second"] if self.active_scenario else self.events_per_second
            delay = 1.0 / eps if eps > 0 else 1.0

            # Generate event
            specific_attack = self.active_scenario["attack_type"] if self.active_scenario else None
            
            event_raw = generate_event(
                threat_rate=self.threat_rate,
                specific_attack=specific_attack
            )
            
            # Predict
            predictions = predictor.predict(event_raw)
            
            # Combine
            event_full = {**event_raw, **predictions}
            del event_full["raw_features"]

            if self.active_scenario:
                self.scenario_events_generated += 1
                if event_full.get("prediction") == "ATTACK":
                    self.scenario_events_flagged += 1
            
            # Process & Store
            event_store.add_event(event_full)
            stats_aggregator.process_event(event_full)
            
            # Broadcast
            await manager.broadcast_event(event_full)

            # Auto-incident evaluation and push
            incident = evaluate_event_for_incident(event_full)
            if incident:
                await manager.broadcast_incident(incident)
            
            # Broadcast stats
            await manager.broadcast_stats(stats_aggregator.get_stats())
            
            await asyncio.sleep(delay)

simulator = NetworkSimulator()
