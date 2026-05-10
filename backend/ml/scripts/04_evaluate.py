from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import joblib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score

from config import (
    BEST_MODEL_PATH,
    METRICS_SUMMARY_PATH,
    MODEL_PATHS,
    OUTPUTS_FIGURES_DIR,
    X_TEST_PATH,
    Y_TEST_PATH,
)
from scripts.common import ensure_parent, save_json
from src.evaluation import compute_metrics, evaluate_model, evaluate_all_models, print_evaluation_summary, plot_confusion_matrix


def _safe_roc_auc(model, x_test: pd.DataFrame, y_test: pd.Series) -> float:
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(x_test)
        if proba.shape[1] == 2:
            return float(roc_auc_score(y_test, proba[:, 1]))
        return float(roc_auc_score(y_test, proba, multi_class="ovr"))
    return float("nan")


def evaluate_models() -> dict[str, dict[str, float]]:
    if not X_TEST_PATH.exists() or not Y_TEST_PATH.exists():
        raise FileNotFoundError("Preprocessed test files missing. Run scripts/02_preprocess.py first.")

    x_test = pd.read_csv(X_TEST_PATH)
    y_test = pd.read_csv(Y_TEST_PATH).iloc[:, 0]

    models = {}
    for model_name, model_path in MODEL_PATHS.items():
        if not model_path.exists():
            raise FileNotFoundError(f"Model artifact missing: {model_path}")
        models[model_name] = joblib.load(model_path)

    results = evaluate_all_models(models, x_test, y_test)
    print_evaluation_summary(results)

    metrics_summary = {}
    for name, result in results.items():
        m = result["metrics"]
        metrics_summary[name] = m
        cm = result["confusion_matrix"]

        fig = plot_confusion_matrix(
            cm,
            labels=["Benign", "Attack"],
            title=f"Confusion Matrix - {name}",
            save_path=OUTPUTS_FIGURES_DIR / f"confusion_matrix_{name}.png",
        )
        plt.close(fig)

    rf_model = models["random_forest"]
    if hasattr(rf_model.named_steps["classifier"], "feature_importances_"):
        importances = rf_model.named_steps["classifier"].feature_importances_
        feature_names = x_test.columns
        importance_df = (
            pd.DataFrame({"feature": feature_names, "importance": importances})
            .sort_values("importance", ascending=False)
            .head(20)
        )
        plt.figure(figsize=(10, 6))
        sns.barplot(data=importance_df, x="importance", y="feature", hue="feature", legend=False)
        plt.title("Top 20 Feature Importances (Random Forest)")
        plt.tight_layout()
        fi_path = OUTPUTS_FIGURES_DIR / "feature_importance_rf.png"
        ensure_parent(fi_path)
        plt.savefig(fi_path)
        plt.close()

    best_model_name = max(metrics_summary, key=lambda name: metrics_summary[name]["recall"])
    best_model_payload = {
        "best_model": best_model_name,
        "metric": "recall",
        "score": metrics_summary[best_model_name]["recall"],
    }

    save_json(metrics_summary, METRICS_SUMMARY_PATH)
    save_json(best_model_payload, BEST_MODEL_PATH)

    print(f"Saved metrics summary to {METRICS_SUMMARY_PATH}")
    print(f"Saved best model info to {BEST_MODEL_PATH}")
    return metrics_summary


if __name__ == "__main__":
    evaluate_models()
