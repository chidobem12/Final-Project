import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_get_metrics():
    """Test getting system metrics."""
    response = client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "events_per_minute" in data
    assert "threats_per_minute" in data
    assert "active_attacks" in data

def test_get_events():
    """Test fetching recent events API."""
    response = client.get("/api/events?limit=10")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_trigger_attack():
    """Test attacking scenario triggering endpoint."""
    payload = {"scenario_id": "ddos_flood"}
    response = client.post("/api/simulate/attack", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "success", "scenario": "ddos_flood"}
