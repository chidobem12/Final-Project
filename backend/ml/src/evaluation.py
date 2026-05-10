from __future__ import annotations

from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report
from sklearn.pipeline import Pipeline


def compute_metrics(
    y_true: np.ndarray | pd.Series,
    y_pred: np.ndarray | pd.Series,
    average: str = "binary",
) -> dict[str, float]:
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, average=average, zero_division=0),
        "recall": recall_score(y_true, y_pred, average=average, zero_division=0),
        "f1": f1_score(y_true, y_pred, average=average, zero_division=0),
    }


def evaluate_model(
    estimator: Pipeline,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    average: str = "binary",
) -> dict[str, Any]:
    y_pred = estimator.predict(X_test)

    metrics = compute_metrics(y_test, y_pred, average=average)
    cm = confusion_matrix(y_test, y_pred)

    return {
        "metrics": metrics,
        "confusion_matrix": cm.tolist(),
        "predictions": y_pred.tolist(),
    }


def evaluate_all_models(
    models: dict[str, Pipeline],
    X_test: pd.DataFrame,
    y_test: pd.Series,
    average: str = "binary",
) -> dict[str, dict[str, Any]]:
    results = {}

    for name, model in models.items():
        results[name] = evaluate_model(model, X_test, y_test, average=average)

    return results


def print_evaluation_summary(
    results: dict[str, dict[str, Any]],
) -> None:
    print(f"{'Model':<12} {'Accuracy':>10} {'Precision':>10} {'Recall':>10} {'F1':>10}")
    print("-" * 52)

    for name, result in results.items():
        m = result["metrics"]
        print(f"{name:<12} {m['accuracy']:>10.4f} {m['precision']:>10.4f} {m['recall']:>10.4f} {m['f1']:>10.4f}")

    print("-" * 52)


def plot_confusion_matrix(
    cm: np.ndarray | list[list[int]],
    labels: list[str] | None = None,
    title: str = "Confusion Matrix",
    save_path: Path | str | None = None,
) -> plt.Figure:
    cm = np.array(cm)
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax,
                xticklabels=labels or ["Negative", "Positive"],
                yticklabels=labels or ["Negative", "Positive"])
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(title)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)
        plt.close(fig)
    return fig


def plot_all_confusion_matrices(
    results: dict[str, dict[str, Any]],
    save_dir: Path | str | None = None,
    labels: list[str] | None = None,
) -> None:
    save_dir = Path(save_dir) if save_dir else Path("models")
    save_dir.mkdir(parents=True, exist_ok=True)

    for name, result in results.items():
        cm = result["confusion_matrix"]
        title = f"{name.upper()} - Confusion Matrix"
        save_path = save_dir / f"confusion_matrix_{name}.png"
        plot_confusion_matrix(cm, labels=labels, title=title, save_path=save_path)
        print(f"Saved: {save_path}")


def per_class_breakdown(
    y_true: np.ndarray | pd.Series,
    y_pred: np.ndarray | pd.Series,
    labels: list[str] | None = None,
) -> pd.DataFrame:
    report = classification_report(y_true, y_pred, target_names=labels, output_dict=True, zero_division=0)
    return pd.DataFrame(report).transpose()


def get_feature_importance(
    estimator: Pipeline,
    feature_names: list[str],
) -> pd.DataFrame:
    clf = estimator.named_steps["classifier"]
    if not hasattr(clf, "feature_importances_"):
        raise ValueError("Model does not support feature importance (requires tree-based model)")
    importance = clf.feature_importances_
    df = pd.DataFrame({"feature": feature_names, "importance": importance})
    return df.sort_values("importance", ascending=False).reset_index(drop=True)


def select_top_features(
    importance_df: pd.DataFrame,
    k: int,
) -> list[str]:
    return importance_df.head(k)["feature"].tolist()
