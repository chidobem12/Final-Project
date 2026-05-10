from __future__ import annotations

from pathlib import Path
from typing import Sequence

import pandas as pd


def load_csv(filepath: str | Path, **kwargs: object) -> pd.DataFrame:
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"CSV not found: {filepath}")
    return pd.read_csv(filepath, **kwargs)


def validate_columns(df: pd.DataFrame, required: Sequence[str]) -> list[str]:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return list(required)


def report_shape(df: pd.DataFrame, name: str = "") -> None:
    label = f" {name}" if name else ""
    print(f"Dataset{label}: {df.shape[0]} rows x {df.shape[1]} columns")


def ingest_csv(
    filepath: str | Path,
    required: Sequence[str] | None = None,
    **kwargs: object,
) -> pd.DataFrame:
    df = load_csv(filepath, **kwargs)
    if required:
        validate_columns(df, required)
    report_shape(df, name=str(filepath))
    return df
