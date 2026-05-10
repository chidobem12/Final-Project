"""Shared pipeline utilities for data loading, cleaning, feature engineering, and persistence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from config import TARGET_COLUMN


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def find_csv_files(raw_dir: Path) -> list[Path]:
    return sorted(raw_dir.glob("*.csv"))


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    cleaned.columns = cleaned.columns.str.strip()

    if TARGET_COLUMN in cleaned.columns:
        cleaned[TARGET_COLUMN] = cleaned[TARGET_COLUMN].astype(str).str.strip()

    cleaned = cleaned.replace([np.inf, -np.inf], np.nan)
    cleaned = cleaned.dropna(axis=1, how="all")
    cleaned = cleaned.fillna(0)
    return cleaned


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def save_json(payload: dict, path: Path) -> None:
    ensure_parent(path)
    with path.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, indent=2)


def align_features(features: pd.DataFrame, required_columns: Iterable[str]) -> pd.DataFrame:
    aligned = features.copy()
    aligned.columns = aligned.columns.str.strip()

    for column in required_columns:
        if column not in aligned.columns:
            aligned[column] = 0

    return aligned[list(required_columns)]
