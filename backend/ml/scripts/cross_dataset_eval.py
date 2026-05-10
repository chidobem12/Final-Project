#!/usr/bin/env python3
"""Cross-dataset validation: evaluate CICIDS2017-trained models on other datasets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import joblib

from src.preprocessing import clean
from src.evaluation import compute_metrics
from config import DATASET_CONFIGS, MODELS_DIR

CICIDS_LABEL = " Label"


def get_model_feature_names(model: Any) -> list[str]:
    return model.named_steps["scaler"].feature_names_in_.tolist()


def evaluate_on_kdd(models: dict[str, Any], expected_features: list[str], sample_size: int = 30000) -> dict[str, Any]:
    kdd_cols = [
        'duration', 'protocol_type', 'service', 'flag', 'src_bytes', 'dst_bytes',
        'land', 'wrong_fragment', 'urgent', 'hot', 'num_failed_logins', 'logged_in',
        'num_compromised', 'root_shell', 'su_attempted', 'num_root', 'num_file_creations',
        'num_shells', 'num_access_files', 'num_outbound_cmds', 'is_host_login',
        'is_guest_login', 'count', 'srv_count', 'serror_rate', 'srv_serror_rate',
        'rerror_rate', 'srv_rerror_rate', 'same_srv_rate', 'diff_srv_rate',
        'srv_diff_host_rate', 'dst_host_count', 'dst_host_srv_count',
        'dst_host_same_srv_rate', 'dst_host_diff_srv_rate', 'dst_host_same_src_port_rate',
        'dst_host_srv_diff_host_rate', 'dst_host_serror_rate', 'dst_host_srv_serror_rate',
        'dst_host_rerror_rate', 'dst_host_srv_rerror_rate', 'label'
    ]

    cfg = DATASET_CONFIGS["kddcup99"]
    df = pd.read_csv(cfg["raw_dir"] / "kddcup.data_10_percent", header=None, names=kdd_cols)

    df["label_binary"] = df["label"].apply(lambda x: 0 if x == "normal." else 1)
    df = df.drop(columns=["label"])

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    numeric_cols.remove("label_binary")

    for col in numeric_cols:
        df[col] = df[col].astype(float)

    df = clean(df, null_strategy="drop")

    for col in numeric_cols:
        min_val, max_val = df[col].min(), df[col].max()
        if max_val > min_val:
            df[col] = (df[col] - min_val) / (max_val - min_val)

    data = {}
    for feat in expected_features:
        if feat in df.columns:
            series = df[feat].copy()
            series = pd.to_numeric(series, errors='coerce').fillna(0.0)
            data[feat] = series.values
        else:
            data[feat] = np.zeros(len(df))

    result_df = pd.DataFrame(data, columns=expected_features)
    result_df = result_df.fillna(0.0)
    result_df = result_df.replace([np.inf, -np.inf], 0.0)

    assert not result_df.isna().any().any(), "NaN still present"
    assert not np.isinf(result_df.values).any(), "Inf still present"

    result_df[CICIDS_LABEL] = df["label_binary"].values

    if len(result_df) > sample_size:
        result_df = result_df.sample(n=sample_size, random_state=42)

    return evaluate_models(models, result_df)


def evaluate_on_unsw(models: dict[str, Any], expected_features: list[str], sample_size: int = 20000) -> dict[str, Any]:
    feature_mapping = {
        'dst_bytes': 'dbytes',
        'src_bytes': 'sbytes',
    }

    unsw_cols = [f'col_{i}' for i in range(49)]

    cfg = DATASET_CONFIGS["unsw_nb15"]
    df = pd.read_csv(cfg["raw_dir"] / "UNSW-NB15_1.csv", header=None, names=unsw_cols)

    df["label_binary"] = df.iloc[:, -1].apply(lambda x: 0 if str(x).lower() == "normal" else 1)

    numeric_df = df.select_dtypes(include=[np.number]).copy()
    numeric_df["label_binary"] = df["label_binary"]

    for col in numeric_df.columns:
        if col != "label_binary":
            min_val, max_val = numeric_df[col].min(), numeric_df[col].max()
            if max_val > min_val:
                numeric_df[col] = (numeric_df[col] - min_val) / (max_val - min_val)

    numeric_df = numeric_df.dropna()

    data = {}
    for feat in expected_features:
        if feat in numeric_df.columns:
            series = numeric_df[feat].copy()
            series = pd.to_numeric(series, errors='coerce').fillna(0.0)
            data[feat] = series.values
        elif feat in feature_mapping and feature_mapping[feat] in numeric_df.columns:
            series = numeric_df[feature_mapping[feat]].copy()
            series = pd.to_numeric(series, errors='coerce').fillna(0.0)
            data[feat] = series.values
        else:
            data[feat] = np.zeros(len(numeric_df))

    result_df = pd.DataFrame(data, columns=expected_features)
    result_df = result_df.fillna(0.0)
    result_df = result_df.replace([np.inf, -np.inf], 0.0)

    assert not result_df.isna().any().any(), "NaN still present"

    result_df[CICIDS_LABEL] = numeric_df["label_binary"].values

    if len(result_df) > sample_size:
        result_df = result_df.sample(n=sample_size, random_state=42)

    return evaluate_models(models, result_df)


def evaluate_models(models: dict[str, Any], df: pd.DataFrame) -> dict[str, Any]:
    label_col = CICIDS_LABEL

    if label_col not in df.columns:
        raise ValueError(f"Label column {label_col} not found in df")

    y_true = df[label_col].values
    X = df.drop(columns=[label_col], errors="ignore")

    results = {}
    for name, model in models.items():
        y_pred = model.predict(X)
        metrics = compute_metrics(y_true, y_pred)
        results[name] = {
            "metrics": metrics,
            "n_samples": len(y_true),
            "attack_ratio": float(y_true.mean()),
            "n_features_used": X.shape[1],
        }

    return results


def main() -> None:
    cicids_models_dir = MODELS_DIR

    print("Loading CICIDS2017-trained models...")
    models = {
        "logistic_regression": joblib.load(cicids_models_dir / "logistic_regression.joblib"),
        "random_forest": joblib.load(cicids_models_dir / "random_forest.joblib"),
        "gradient_boosting": joblib.load(cicids_models_dir / "gradient_boosting.joblib"),
    }

    expected_features = get_model_feature_names(models["logistic_regression"])
    print(f"Model expects {len(expected_features)} features")

    print("\n=== Evaluating on KDD Cup 99 ===")
    kdd_results = evaluate_on_kdd(models, expected_features)

    for name, result in kdd_results.items():
        m = result["metrics"]
        print(f"{name}: Acc={m['accuracy']:.4f}, Prec={m['precision']:.4f}, Rec={m['recall']:.4f}, F1={m['f1']:.4f}")

    print("\n=== Evaluating on UNSW-NB15 ===")
    unsw_results = evaluate_on_unsw(models, expected_features)

    for name, result in unsw_results.items():
        m = result["metrics"]
        print(f"{name}: Acc={m['accuracy']:.4f}, Prec={m['precision']:.4f}, Rec={m['recall']:.4f}, F1={m['f1']:.4f}")

    output = {
        "kdd_cup_99": kdd_results,
        "unsw_nb15": unsw_results,
    }

    with open(cicids_models_dir / "cross_dataset_results.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved to {cicids_models_dir / 'cross_dataset_results.json'}")


if __name__ == "__main__":
    main()
