"""Preprocess combined data: clean, encode labels, split, normalize, select features, and apply train-only SMOTE."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import joblib
import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from sklearn.feature_selection import SelectKBest, mutual_info_classif
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

from config import (
    RANDOM_STATE,
    RAW_COMBINED_PATH,
    SAMPLE_SIZE,
    SCALER_PATH,
    SELECTED_FEATURES_PATH,
    TARGET_COLUMN,
    TEST_SIZE,
    X_TEST_PATH,
    X_TRAIN_PATH,
    Y_TEST_PATH,
    Y_TRAIN_PATH,
)
from scripts.common import clean_dataframe, ensure_parent


def preprocess_data(
    input_path: Path = RAW_COMBINED_PATH,
    sample_size: int | None = SAMPLE_SIZE,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path, low_memory=False)
    df = clean_dataframe(df)

    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Target column '{TARGET_COLUMN}' not found in combined dataset")

    if sample_size and len(df) > sample_size:
        df = df.sample(n=sample_size, random_state=RANDOM_STATE)

    y_raw = df[TARGET_COLUMN].astype(str).str.strip()
    x_raw = df.drop(columns=[TARGET_COLUMN])

    numeric_x = x_raw.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0)

    label_encoder = LabelEncoder()
    y_encoded = pd.Series(label_encoder.fit_transform(y_raw), name=TARGET_COLUMN)

    x_train, x_test, y_train, y_test = train_test_split(
        numeric_x,
        y_encoded,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y_encoded,
    )

    scaler = StandardScaler()
    x_train_scaled = pd.DataFrame(
        scaler.fit_transform(x_train),
        columns=x_train.columns,
        index=x_train.index,
    )
    x_test_scaled = pd.DataFrame(
        scaler.transform(x_test),
        columns=x_test.columns,
        index=x_test.index,
    )

    k_features = min(30, x_train_scaled.shape[1])
    selector = SelectKBest(score_func=mutual_info_classif, k=k_features)
    selector.fit(x_train_scaled, y_train)
    selected_columns = x_train_scaled.columns[selector.get_support()].tolist()

    x_train_selected = x_train_scaled[selected_columns]
    x_test_selected = x_test_scaled[selected_columns]

    # SMOTE is applied only to training data to avoid test-set leakage.
    smote = SMOTE(random_state=RANDOM_STATE)
    x_train_resampled, y_train_resampled = smote.fit_resample(x_train_selected, y_train)

    x_train_out = pd.DataFrame(x_train_resampled, columns=selected_columns)
    x_test_out = x_test_selected.reset_index(drop=True)
    y_train_out = pd.Series(y_train_resampled, name=TARGET_COLUMN)
    y_test_out = y_test.reset_index(drop=True)

    for path in [X_TRAIN_PATH, X_TEST_PATH, Y_TRAIN_PATH, Y_TEST_PATH, SCALER_PATH, SELECTED_FEATURES_PATH]:
        ensure_parent(path)

    x_train_out.to_csv(X_TRAIN_PATH, index=False)
    x_test_out.to_csv(X_TEST_PATH, index=False)
    y_train_out.to_frame().to_csv(Y_TRAIN_PATH, index=False)
    y_test_out.to_frame().to_csv(Y_TEST_PATH, index=False)

    joblib.dump(scaler, SCALER_PATH)
    with SELECTED_FEATURES_PATH.open("w", encoding="utf-8") as fp:
        json.dump(selected_columns, fp, indent=2)

    print("Saved preprocessed datasets and artifacts:")
    print(f"- {X_TRAIN_PATH}")
    print(f"- {X_TEST_PATH}")
    print(f"- {Y_TRAIN_PATH}")
    print(f"- {Y_TEST_PATH}")
    print(f"- {SCALER_PATH}")
    print(f"- {SELECTED_FEATURES_PATH}")

    return x_train_out, x_test_out, y_train_out, y_test_out


if __name__ == "__main__":
    preprocess_data()
