from __future__ import annotations

from typing import Any, Sequence

import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, MinMaxScaler, OneHotEncoder


IRRELEVANT_COLS: dict[str, list[str]] = {
    "cicids2017": [
        "Destination Port",
    ],
    "unsw_nb15": [
        "srcip", "sport", "dstip", "dsport",
        "Stime", "Ltime",
    ],
    "kddcup99": [],
}

DEFAULT_DROP_COLS: list[str] = sorted(
    {c for cols in IRRELEVANT_COLS.values() for c in cols}
)


def drop_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates()
    after = len(df)
    if before != after:
        print(f"  Removed {before - after} duplicate row(s).")
    return df


def handle_nulls(
    df: pd.DataFrame,
    strategy: str = "drop",
    fill_value: object = 0,
) -> pd.DataFrame:
    null_count = df.isnull().sum().sum()
    if null_count == 0:
        return df

    print(f"  Found {null_count} null value(s).")

    if strategy == "drop":
        before = len(df)
        df = df.dropna()
        print(f"  Dropped {before - len(df)} row(s) with nulls.")
    elif strategy == "fill":
        for col in df.columns:
            if df[col].isnull().any():
                if pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = df[col].fillna(fill_value)
                else:
                    df[col] = df[col].fillna("unknown")
        print(f"  Filled {null_count} null(s) with default values.")
    else:
        raise ValueError(f"Unknown null strategy: {strategy!r}")

    return df


def handle_infs(df: pd.DataFrame) -> pd.DataFrame:
    num_cols = df.select_dtypes(include=[np.number]).columns
    inf_mask = np.isinf(df[num_cols])
    inf_count = inf_mask.sum().sum()
    if inf_count == 0:
        return df

    print(f"  Found {inf_count} infinite value(s). Replacing with NaN.")
    df[num_cols] = df[num_cols].replace([np.inf, -np.inf], np.nan)
    before = len(df)
    df = df.dropna(subset=num_cols)
    print(f"  Dropped {before - len(df)} row(s) with infinities.")
    return df


def drop_irrelevant(
    df: pd.DataFrame,
    drop_cols: Sequence[str] | None = None,
    dataset: str | None = None,
) -> pd.DataFrame:
    to_drop: list[str] = []

    if dataset and dataset in IRRELEVANT_COLS:
        to_drop.extend(IRRELEVANT_COLS[dataset])
    if drop_cols:
        to_drop.extend(drop_cols)

    if not to_drop:
        return df

    to_drop = [c for c in to_drop if c in df.columns]
    if not to_drop:
        return df

    print(f"  Dropping irrelevant column(s): {to_drop}")
    return df.drop(columns=to_drop)


def clean(
    df: pd.DataFrame,
    dataset: str | None = None,
    drop_cols: Sequence[str] | None = None,
    null_strategy: str = "drop",
    verbose: bool = True,
) -> pd.DataFrame:
    if df.empty:
        print("  Input DataFrame is empty — nothing to clean.")
        return df

    if verbose:
        print(f"Cleaning: {df.shape[0]} rows x {df.shape[1]} cols")

    df = drop_irrelevant(df, drop_cols=drop_cols, dataset=dataset)
    df = drop_duplicates(df)
    df = handle_infs(df)
    df = handle_nulls(df, strategy=null_strategy)

    if verbose:
        print(f"Result:   {df.shape[0]} rows x {df.shape[1]} cols")

    return df


def auto_categorical_cols(df: pd.DataFrame) -> list[str]:
    return df.select_dtypes(exclude=[np.number]).columns.tolist()


def encode(
    df: pd.DataFrame,
    label_col: str | None = None,
    max_onehot_categories: int = 10,
    ohe_cols: Sequence[str] | None = None,
    label_cols: Sequence[str] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    cat_cols = auto_categorical_cols(df)

    feature_cats = [c for c in cat_cols if c != label_col]

    result = df.copy()
    encoders: dict[str, Any] = {}

    if feature_cats:
        if ohe_cols is not None or label_cols is not None:
            ohe_columns = list(ohe_cols or [])
            label_columns = list(label_cols or [])
        else:
            ohe_columns = [
                c for c in feature_cats
                if df[c].nunique() <= max_onehot_categories
            ]
            label_columns = [
                c for c in feature_cats
                if df[c].nunique() > max_onehot_categories
            ]

        for col in label_columns:
            le = LabelEncoder()
            result[col] = le.fit_transform(result[col].astype(str))
            encoders[col] = le
            print(f"  Label-encoded '{col}' ({df[col].nunique()} classes) -> {col}")

        ohe_infos: list[dict[str, Any]] = []
        for col in ohe_columns:
            ohe = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
            encoded = ohe.fit_transform(result[[col]])
            feature_names = ohe.get_feature_names_out([col])
            ohe_df = pd.DataFrame(
                encoded, columns=feature_names, index=result.index
            )
            result = pd.concat([result, ohe_df], axis=1)
            result = result.drop(columns=[col])
            ohe_infos.append({
                "column": col,
                "encoder": ohe,
                "features": list(feature_names),
                "nunique": int(df[col].nunique()),
            })
            print(
                f"  One-hot-encoded '{col}' "
                f"({df[col].nunique()} classes) -> {list(feature_names)}"
            )
        if ohe_infos:
            encoders["_ohe_"] = ohe_infos

    if label_col and label_col in cat_cols:
        le = LabelEncoder()
        result[label_col] = le.fit_transform(result[label_col].astype(str))
        encoders["_label_"] = le
        print(f"  Label-encoded target '{label_col}' ({df[label_col].nunique()} classes)")

    return result, encoders


def normalise(
    df: pd.DataFrame,
    exclude_cols: Sequence[str] | None = None,
    feature_range: tuple[float, float] = (0, 1),
) -> tuple[pd.DataFrame, MinMaxScaler]:
    exclude = set(exclude_cols or [])
    scale_cols = [
        c for c in df.select_dtypes(include=[np.number]).columns
        if c not in exclude
    ]

    if not scale_cols:
        print("  No numeric columns to normalise.")
        return df.copy(), MinMaxScaler()

    scaler = MinMaxScaler(feature_range=feature_range)
    scaled = scaler.fit_transform(df[scale_cols])
    result = df.copy()
    result[scale_cols] = scaled

    print(f"  MinMax-scaled {len(scale_cols)} numeric column(s) to {feature_range}.")

    mins = result[scale_cols].min()
    maxs = result[scale_cols].max()
    out_of_range = (mins < feature_range[0] - 1e-12) | (maxs > feature_range[1] + 1e-12)
    bad_cols = out_of_range[out_of_range].index.tolist()
    if bad_cols:
        print(f"  WARNING: {len(bad_cols)} column(s) outside [{feature_range[0]}, {feature_range[1]}]: {bad_cols}")
    else:
        print(f"  All {len(scale_cols)} columns verified in [{feature_range[0]}, {feature_range[1]}].")

    return result, scaler


def balance_and_split(
    df: pd.DataFrame,
    label_col: str,
    test_size: float = 0.2,
    random_state: int = 42,
    smote_kwargs: dict[str, Any] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    if label_col not in df.columns:
        raise ValueError(f"Label column '{label_col}' not found in DataFrame.")

    y = df[label_col].values
    X = df.drop(columns=[label_col])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=random_state,
    )

    train_ratio = pd.Series(y_train).value_counts(normalize=True).to_dict()
    print(f"  Stratified split: train={len(X_train)}, test={len(X_test)} "
          f"(class ratio: {train_ratio})")

    before = pd.Series(y_train).value_counts().to_dict()
    min_class_size = pd.Series(y_train).value_counts().min()
    safe_k = max(1, min(5, min_class_size - 1))
    smote = SMOTE(random_state=random_state, k_neighbors=safe_k, **(smote_kwargs or {}))
    X_train_res, y_train_res = smote.fit_resample(X_train, y_train)
    after = pd.Series(y_train_res).value_counts().to_dict()

    print(f"  SMOTE applied: {dict(sorted(before.items()))} -> "
          f"{dict(sorted(after.items()))} (balanced)")

    X_train_res = pd.DataFrame(X_train_res, columns=X_train.columns)
    X_test = pd.DataFrame(X_test, columns=X_train.columns)

    return (
        X_train_res,
        X_test,
        pd.Series(y_train_res, name=label_col),
        pd.Series(y_test, name=label_col),
    )
