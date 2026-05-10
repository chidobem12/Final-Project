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
from src.models import train_logreg_with_cv, train_rf_with_cv, train_gb_with_cv


LOGREG_GRID = {
    "classifier__C": [0.1, 1.0],
    "classifier__penalty": ["l2"],
    "classifier__solver": ["lbfgs"],
}

RF_GRID = {
    "classifier__n_estimators": [50, 100],
    "classifier__max_depth": [10, 20],
    "classifier__min_samples_split": [2, 5],
    "classifier__min_samples_leaf": [1, 2],
}

GB_GRID = {
    "classifier__learning_rate": [0.1],
    "classifier__n_estimators": [50],
    "classifier__max_depth": [3],
}


def train_models() -> dict[str, object]:
    if not X_TRAIN_PATH.exists() or not Y_TRAIN_PATH.exists():
        raise FileNotFoundError("Preprocessed training files missing. Run scripts/02_preprocess.py first.")

    x_train = pd.read_csv(X_TRAIN_PATH)
    y_train = pd.read_csv(Y_TRAIN_PATH).iloc[:, 0]

    sample_size = min(20000, len(x_train))
    x_sample = x_train.sample(n=sample_size, random_state=42)
    y_sample = y_train.loc[x_sample.index]
    print(f"Using {sample_size} samples for training")

    trained_models = {}

    print("\nTraining Logistic Regression with GridSearchCV...")
    estimator, _ = train_logreg_with_cv(x_sample, y_sample, param_grid=LOGREG_GRID, cv=3)
    ensure_parent(MODEL_PATHS["logistic_regression"])
    joblib.dump(estimator, MODEL_PATHS["logistic_regression"])
    print(f"Saved model: {MODEL_PATHS['logistic_regression']}")
    trained_models["logistic_regression"] = estimator

    print("\nTraining Random Forest with GridSearchCV...")
    estimator, _ = train_rf_with_cv(x_sample, y_sample, param_grid=RF_GRID, cv=3)
    ensure_parent(MODEL_PATHS["random_forest"])
    joblib.dump(estimator, MODEL_PATHS["random_forest"])
    print(f"Saved model: {MODEL_PATHS['random_forest']}")
    trained_models["random_forest"] = estimator

    print("\nTraining Gradient Boosting with GridSearchCV...")
    estimator, _ = train_gb_with_cv(x_sample, y_sample, param_grid=GB_GRID, cv=3)
    ensure_parent(MODEL_PATHS["gradient_boosting"])
    joblib.dump(estimator, MODEL_PATHS["gradient_boosting"])
    print(f"Saved model: {MODEL_PATHS['gradient_boosting']}")
    trained_models["gradient_boosting"] = estimator

    return trained_models


if __name__ == "__main__":
    train_models()
