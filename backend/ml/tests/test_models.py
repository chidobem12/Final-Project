"""Tests for model training artifacts and prediction output shape."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_model_files_exist_and_prediction_shape(tmp_path: Path, monkeypatch):
    preprocess = load_module(Path("scripts/02_preprocess.py"), "preprocess_for_models")
    train = load_module(Path("scripts/03_train.py"), "train_script")

    records = []
    for i in range(120):
        records.append(
            {
                "f1": i,
                "f2": i % 7,
                "f3": (i * 3) % 11,
                "Label": "BENIGN" if i < 80 else "ATTACK",
            }
        )

    raw_path = tmp_path / "raw_combined.csv"
    pd.DataFrame(records).to_csv(raw_path, index=False)

    monkeypatch.setattr(preprocess, "X_TRAIN_PATH", tmp_path / "X_train.csv")
    monkeypatch.setattr(preprocess, "X_TEST_PATH", tmp_path / "X_test.csv")
    monkeypatch.setattr(preprocess, "Y_TRAIN_PATH", tmp_path / "y_train.csv")
    monkeypatch.setattr(preprocess, "Y_TEST_PATH", tmp_path / "y_test.csv")
    monkeypatch.setattr(preprocess, "SCALER_PATH", tmp_path / "scaler.joblib")
    monkeypatch.setattr(preprocess, "SELECTED_FEATURES_PATH", tmp_path / "selected_features.json")

    preprocess.preprocess_data(input_path=raw_path, sample_size=None)

    model_dir = tmp_path / "models"
    model_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(train, "X_TRAIN_PATH", tmp_path / "X_train.csv")
    monkeypatch.setattr(train, "Y_TRAIN_PATH", tmp_path / "y_train.csv")
    monkeypatch.setattr(
        train,
        "MODEL_PATHS",
        {
            "logistic_regression": model_dir / "logistic_regression.joblib",
            "random_forest": model_dir / "random_forest.joblib",
            "gradient_boosting": model_dir / "gradient_boosting.joblib",
        },
    )

    models = train.train_models()

    for model_path in train.MODEL_PATHS.values():
        assert model_path.exists()

    x_test = pd.read_csv(tmp_path / "X_test.csv")
    preds = models["logistic_regression"].predict(x_test)
    assert preds.shape[0] == x_test.shape[0]
