from typing import Dict, Any
import json
import os
import time

class StatsAggregator:
    def __init__(self):
        self.start_time = time.time()
        self.events_last_minute = []
        self.threats_last_minute = []
        self.active_attacks = set()
        self.total_events_today = 0
        self.total_threats_today = 0
        self.training_metrics = self._load_training_metrics()

    def _load_training_metrics(self) -> Dict[str, Any]:
        metrics_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../outputs/metrics/metrics_summary.json")
        )
        if not os.path.exists(metrics_path):
            return {}
        with open(metrics_path, "r", encoding="utf-8") as metrics_file:
            return json.load(metrics_file)

    def process_event(self, event: Dict[str, Any]):
        now = time.time()
        self.events_last_minute.append(now)
        self.total_events_today += 1
        
        is_threat = event.get("prediction") == "ATTACK"
        if is_threat:
            self.threats_last_minute.append(now)
            self.total_threats_today += 1
            if event.get("attack_type") != "Normal":
                self.active_attacks.add(event.get("attack_type"))
                
        # Clean up old events
        one_min_ago = now - 60
        self.events_last_minute = [t for t in self.events_last_minute if t > one_min_ago]
        self.threats_last_minute = [t for t in self.threats_last_minute if t > one_min_ago]
        
    def get_stats(self) -> Dict[str, Any]:
        events_pm = len(self.events_last_minute)
        threats_pm = len(self.threats_last_minute)
        threat_rate = (threats_pm / events_pm * 100) if events_pm > 0 else 0.0
        
        return {
            "events_per_minute": events_pm,
            "threats_per_minute": threats_pm,
            "threat_rate_percent": round(threat_rate, 2),
            "active_attacks": list(self.active_attacks),
            "training_metrics": self.training_metrics,
            "total_events_today": self.total_events_today,
            "total_threats_today": self.total_threats_today,
            "uptime_seconds": int(time.time() - self.start_time)
        }

stats_aggregator = StatsAggregator()
