from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


LOGREG_PARAM_GRID: dict[str, list[Any]] = {
    "classifier__C": [0.01, 0.1, 1.0, 10.0],
    "classifier__penalty": ["l1", "l2"],
    "classifier__solver": ["liblinear", "saga"],
}


def build_logreg_pipeline() -> Pipeline:
    return Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression(max_iter=1000, random_state=42)),
    ])


def train_logreg_with_cv(
    X: pd.DataFrame,
    y: pd.Series,
    param_grid: dict[str, list[Any]] | None = None,
    cv: int = 5,
    scoring: str = "accuracy",
    n_jobs: int = -1,
) -> tuple[Pipeline, GridSearchCV]:
    pipeline = build_logreg_pipeline()

    if param_grid is None:
        param_grid = LOGREG_PARAM_GRID.copy()

    grid_search = GridSearchCV(
        estimator=pipeline,
        param_grid=param_grid,
        cv=cv,
        scoring=scoring,
        n_jobs=n_jobs,
        return_train_score=True,
        verbose=1,
    )

    grid_search.fit(X, y)

    print(f"\nBest params: {grid_search.best_params_}")
    print(f"Best {scoring}: {grid_search.best_score_:.4f}")

    return grid_search.best_estimator_, grid_search


def evaluate_cv_scores(
    estimator: Pipeline,
    X: pd.DataFrame,
    y: pd.Series,
    cv: int = 5,
    scoring: str = "accuracy",
) -> dict[str, Any]:
    scores = cross_val_score(estimator, X, y, cv=cv, scoring=scoring)

    return {
        "scores": scores,
        "mean": scores.mean(),
        "std": scores.std(),
    }


RF_PARAM_GRID: dict[str, list[Any]] = {
    "classifier__n_estimators": [50, 100, 200],
    "classifier__max_depth": [5, 10, 20, None],
    "classifier__min_samples_split": [2, 5, 10],
    "classifier__min_samples_leaf": [1, 2, 4],
}


def build_rf_pipeline() -> Pipeline:
    return Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", RandomForestClassifier(random_state=42, n_jobs=-1)),
    ])


def train_rf_with_cv(
    X: pd.DataFrame,
    y: pd.Series,
    param_grid: dict[str, list[Any]] | None = None,
    cv: int = 5,
    scoring: str = "accuracy",
    n_jobs: int = -1,
) -> tuple[Pipeline, GridSearchCV]:
    pipeline = build_rf_pipeline()

    if param_grid is None:
        param_grid = RF_PARAM_GRID.copy()

    grid_search = GridSearchCV(
        estimator=pipeline,
        param_grid=param_grid,
        cv=cv,
        scoring=scoring,
        n_jobs=n_jobs,
        return_train_score=True,
        verbose=1,
    )

    grid_search.fit(X, y)

    print(f"\nBest params: {grid_search.best_params_}")
    print(f"Best {scoring}: {grid_search.best_score_:.4f}")

    return grid_search.best_estimator_, grid_search


GB_PARAM_GRID: dict[str, list[Any]] = {
    "classifier__learning_rate": [0.01, 0.1, 0.2],
    "classifier__n_estimators": [50, 100, 200],
    "classifier__max_depth": [3, 5, 7],
    "classifier__subsample": [0.8, 1.0],
}


def build_gb_pipeline() -> Pipeline:
    return Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", GradientBoostingClassifier(random_state=42)),
    ])


def train_gb_with_cv(
    X: pd.DataFrame,
    y: pd.Series,
    param_grid: dict[str, list[Any]] | None = None,
    cv: int = 5,
    scoring: str = "accuracy",
    n_jobs: int = -1,
) -> tuple[Pipeline, GridSearchCV]:
    pipeline = build_gb_pipeline()

    if param_grid is None:
        param_grid = GB_PARAM_GRID.copy()

    grid_search = GridSearchCV(
        estimator=pipeline,
        param_grid=param_grid,
        cv=cv,
        scoring=scoring,
        n_jobs=n_jobs,
        return_train_score=True,
        verbose=1,
    )

    grid_search.fit(X, y)

    print(f"\nBest params: {grid_search.best_params_}")
    print(f"Best {scoring}: {grid_search.best_score_:.4f}")

    return grid_search.best_estimator_, grid_search
