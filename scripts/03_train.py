"""Train three classifiers sequentially and persist model artifacts for evaluation and serving."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import joblib
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression

from config import MODEL_PATHS, X_TRAIN_PATH, Y_TRAIN_PATH
from scripts.common import ensure_parent


def train_models() -> dict[str, object]:
    if not X_TRAIN_PATH.exists() or not Y_TRAIN_PATH.exists():
        raise FileNotFoundError("Preprocessed training files missing. Run scripts/02_preprocess.py first.")

    x_train = pd.read_csv(X_TRAIN_PATH)
    y_train = pd.read_csv(Y_TRAIN_PATH).iloc[:, 0]

    models = {
        "logistic_regression": LogisticRegression(max_iter=1000, n_jobs=None),
        "random_forest": RandomForestClassifier(
            n_estimators=200,
            random_state=42,
            n_jobs=-1,
            class_weight="balanced",
        ),
        "gradient_boosting": GradientBoostingClassifier(random_state=42),
    }

    trained_models: dict[str, object] = {}
    for name, model in models.items():
        print(f"Training {name}...")
        model.fit(x_train, y_train)
        ensure_parent(MODEL_PATHS[name])
        joblib.dump(model, MODEL_PATHS[name])
        print(f"Saved model: {MODEL_PATHS[name]}")
        trained_models[name] = model

    return trained_models


if __name__ == "__main__":
    train_models()
