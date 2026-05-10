from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from config import MODEL_PATHS, SCALER_PATH, SELECTED_FEATURES_PATH
from scripts.common import align_features, clean_dataframe


def load_artifacts() -> tuple[object, list[str], dict[str, object]]:
    missing = [
        str(path)
        for path in [SCALER_PATH, SELECTED_FEATURES_PATH, *MODEL_PATHS.values()]
        if not path.exists()
    ]
    if missing:
        raise FileNotFoundError("Missing required artifacts:\n" + "\n".join(missing))

    scaler = joblib.load(SCALER_PATH)
    with SELECTED_FEATURES_PATH.open("r", encoding="utf-8") as fp:
        selected_features = json.load(fp)

    models = {name: joblib.load(path) for name, path in MODEL_PATHS.items()}
    return scaler, selected_features, models


def predict_from_csv(input_csv: Path, model_name: str = "random_forest") -> pd.DataFrame:
    scaler, selected_features, models = load_artifacts()

    if model_name not in models:
        raise ValueError(f"Model '{model_name}' not found. Available: {list(models)}")

    incoming = pd.read_csv(input_csv, low_memory=False)
    incoming = clean_dataframe(incoming)

    if "Label" in incoming.columns:
        incoming = incoming.drop(columns=["Label"])

    numeric_incoming = incoming.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0)

    scaler_columns = list(getattr(scaler, "feature_names_in_", numeric_incoming.columns.tolist()))
    scaled_input = align_features(numeric_incoming, scaler_columns)
    scaled_all = pd.DataFrame(
        scaler.transform(scaled_input),
        columns=scaler_columns,
        index=scaled_input.index,
    )

    aligned = align_features(scaled_all, selected_features)

    model = models[model_name]
    predictions = model.predict(aligned)

    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(aligned)
        confidence = proba.max(axis=1)
    else:
        confidence = np.ones(len(predictions))

    result = incoming.copy()
    result["Prediction"] = predictions
    result["Confidence"] = confidence
    return result
