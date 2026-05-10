import io
from typing import Any

import pandas as pd
from fastapi import APIRouter, File, UploadFile, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from .ws_handler import manager
from ..ml.predictor import predictor
from ..simulator.packet_generator import generate_attack_features
from ..simulator.network_simulator import simulator
from ..data.event_store import event_store
from ..data.stats_aggregator import stats_aggregator

router = APIRouter()

@router.websocket("/ws/threats")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # We don't really expect clients to send data, but we keep the connection open
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.get("/api/metrics")
async def get_metrics():
    return stats_aggregator.get_stats()

@router.get("/api/events")
async def get_events(limit: int = 100):
    return event_store.get_recent(limit)

@router.get("/api/stats")
async def get_stats():
    return stats_aggregator.get_stats()

class ScenarioRequest(BaseModel):
    scenario_id: str

@router.post("/api/simulate/attack")
async def trigger_attack(request: ScenarioRequest):
    simulator.trigger_scenario(request.scenario_id)
    return {"status": "success", "scenario": request.scenario_id}


@router.post("/api/simulate/stop")
async def stop_scenario():
    return simulator.stop_scenario()

@router.post("/api/simulate/pause")
async def pause_simulation():
    simulator.pause()
    return {"status": "paused"}

@router.post("/api/simulate/resume")
async def resume_simulation():
    simulator.resume()
    return {"status": "resumed"}


@router.get("/api/debug/test-scenarios")
async def test_scenarios() -> dict[str, Any]:
    attack_types = [
        "DDoS",
        "DoS Hulk",
        "DoS GoldenEye",
        "Port Scan",
        "Brute Force",
        "Botnet C2",
        "Web Attack",
        "SQL Injection",
        "XSS",
        "Infiltration",
        "Exfiltration",
        "Zero-Day",
    ]
    samples_per_attack = 24
    results: dict[str, Any] = {}

    for attack_type in attack_types:
        two_of_three_hits = 0
        unanimous_misses = 0
        per_model_hits = {
            "logistic_regression": 0,
            "random_forest": 0,
            "gradient_boosting": 0,
        }

        for _ in range(samples_per_attack):
            event = {
                "raw_features": generate_attack_features(attack_type),
                "true_label": attack_type,
            }
            pred = predictor.predict(event)
            votes = pred.get("model_votes", {})
            attack_votes = sum(1 for model in votes.values() if model.get("prediction") == 1)
            if attack_votes >= 2:
                two_of_three_hits += 1
            if attack_votes == 0:
                unanimous_misses += 1
            for model_name in per_model_hits:
                if votes.get(model_name, {}).get("prediction") == 1:
                    per_model_hits[model_name] += 1

        results[attack_type] = {
            "samples": samples_per_attack,
            "two_of_three_hit_rate": round(two_of_three_hits / samples_per_attack, 4),
            "unanimous_miss_rate": round(unanimous_misses / samples_per_attack, 4),
            "per_model_attack_rate": {
                key: round(value / samples_per_attack, 4)
                for key, value in per_model_hits.items()
            },
        }

    return {"results": results}


@router.post("/api/upload/csv")
async def upload_csv(file: UploadFile = File(...)):
    contents = await file.read()
    df = pd.read_csv(io.BytesIO(contents))
    results = predictor.predict_dataframe(df)
    attacks = sum(1 for r in results if r["prediction"] == "ATTACK")
    return {
        "filename": file.filename,
        "total_rows": len(results),
        "attacks_detected": attacks,
        "normal_classified": len(results) - attacks,
        "attack_rate": round(attacks / len(results), 4) if results else 0,
        "results": results,
    }

