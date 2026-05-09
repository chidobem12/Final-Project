"""Tests for preprocessing pipeline behavior."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pandas as pd


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_cleaning_label_encoding_and_smote_scope(tmp_path: Path, monkeypatch):
    script = load_module(Path("scripts/02_preprocess.py"), "preprocess_script")

    rows = []
    for index in range(60):
        label = " BENIGN " if index < 40 else " ATTACK "
        rows.append({" f1 ": index, "f2": float(index) if index % 10 else float("inf"), "Label": label})

    input_path = tmp_path / "raw_combined.csv"
    pd.DataFrame(rows).to_csv(input_path, index=False)

    monkeypatch.setattr(script, "X_TRAIN_PATH", tmp_path / "X_train.csv")
    monkeypatch.setattr(script, "X_TEST_PATH", tmp_path / "X_test.csv")
    monkeypatch.setattr(script, "Y_TRAIN_PATH", tmp_path / "y_train.csv")
    monkeypatch.setattr(script, "Y_TEST_PATH", tmp_path / "y_test.csv")
    monkeypatch.setattr(script, "SCALER_PATH", tmp_path / "scaler.joblib")
    monkeypatch.setattr(script, "SELECTED_FEATURES_PATH", tmp_path / "selected_features.json")

    x_train, x_test, y_train, y_test = script.preprocess_data(input_path=input_path, sample_size=None)

    assert "f1" in x_train.columns
    assert "f2" in x_train.columns
    assert y_train.dtype.kind in {"i", "u"}

    expected_test_size = int(len(rows) * script.TEST_SIZE)
    assert len(y_test) == expected_test_size
    assert len(y_train) > (len(rows) - expected_test_size)

    with (tmp_path / "selected_features.json").open("r", encoding="utf-8") as fp:
        selected = json.load(fp)
    assert isinstance(selected, list)
    assert len(selected) > 0
