import os
import joblib
import json
import logging

logger = logging.getLogger(__name__)

class ModelManager:
    def __init__(self):
        self.models = {}
        self.scaler = None
        self.features = []

    def load_models(self):
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../models"))
        
        try:
            self.models["logistic_regression"] = joblib.load(os.path.join(base_path, "logistic_regression.joblib"))
            self.models["random_forest"] = joblib.load(os.path.join(base_path, "random_forest.joblib"))
            self.models["gradient_boosting"] = joblib.load(os.path.join(base_path, "gradient_boosting.joblib"))
            self.scaler = joblib.load(os.path.join(base_path, "scaler.joblib"))
            
            with open(os.path.join(base_path, "selected_features.json")) as f:
                self.features = json.load(f)
                
            logger.info("Models successfully loaded")
        except Exception as e:
            logger.exception("Error loading models: %s", e)

model_manager = ModelManager()
