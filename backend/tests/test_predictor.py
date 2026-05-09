import pytest
from backend.ml.predictor import predictor
from backend.ml.model_loader import model_manager

def test_mock_predictor():
    """Test the ML predictor fallback behavior."""
    event = {
        "raw_features": {},
        "true_label": "Botnet C2"
    }
    
    # Normally this uses models, but we'll test the output schema
    result = predictor.predict(event)
    
    assert "prediction" in result
    assert "severity" in result
    assert "risk_score" in result
    assert "confidence" in result
    assert "model_votes" in result
    
def test_predictor_normal_traffic():
    """Test predictor with normal mock traffic logic."""
    event = {
        "raw_features": {},
        "true_label": "Normal"
    }
    result = predictor.predict(event)
    assert result["prediction"] == "NORMAL"
    assert result["severity"] == "NONE"
