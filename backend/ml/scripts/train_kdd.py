#!/usr/bin/env python3
"""Train models on KDD Cup 99 dataset."""

from __future__ import annotations

import joblib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from config import DATASET_CONFIGS

KDD_COLS = [
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

LABEL_COL = 'label'


def main() -> None:
    cfg = DATASET_CONFIGS["kddcup99"]
    models_dir = cfg["models_dir"]
    models_dir.mkdir(parents=True, exist_ok=True)

    print("Loading KDD Cup 99 data...")
    df = pd.read_csv(cfg["raw_dir"] / "kddcup.data_10_percent", header=None, names=KDD_COLS)
    print(f"Original: {df.shape}")

    df['label_binary'] = df['label'].apply(lambda x: 0 if x == 'normal.' else 1)
    df = df.drop(columns=['label'])

    for col in ['protocol_type', 'service', 'flag']:
        df[col] = df[col].astype('category').cat.codes

    X = df.drop(columns=['label_binary'])
    y = df['label_binary']

    X = X.replace([np.inf, -np.inf], np.nan).fillna(0)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X_scaled = pd.DataFrame(X_scaled, columns=X.columns)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"Train: {len(X_train)}, Test: {len(X_test)}")
    print(f"Attack ratio: {y.mean():.2%}")

    sample_size = min(50000, len(X_train))
    idx = np.random.RandomState(42).choice(len(X_train), sample_size, replace=False)
    X_sample = X_train.iloc[idx]
    y_sample = y_train.iloc[idx]

    models = [
        ('logreg', LogisticRegression(max_iter=500, random_state=42)),
        ('rf', RandomForestClassifier(n_estimators=50, max_depth=15, random_state=42, n_jobs=-1)),
        ('gb', GradientBoostingClassifier(n_estimators=50, max_depth=5, random_state=42)),
    ]

    results = {}
    for name, clf in models:
        print(f"\nTraining {name}...")
        clf.fit(X_sample, y_sample)

        y_pred = clf.predict(X_test)
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, zero_division=0),
            'recall': recall_score(y_test, y_pred, zero_division=0),
            'f1': f1_score(y_test, y_pred, zero_division=0),
        }
        results[name] = metrics
        print(f"{name}: Acc={metrics['accuracy']:.4f}, Rec={metrics['recall']:.4f}")

        pipeline = Pipeline([('scaler', StandardScaler()), ('classifier', type(clf)(**clf.get_params()))])
        pipeline.fit(X_sample, y_sample)
        joblib.dump(pipeline, models_dir / f'{name}.joblib')

    with open(models_dir / 'evaluation_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    joblib.dump(scaler, models_dir / 'scaler.joblib')

    print(f"\nSaved to {models_dir}/")


if __name__ == '__main__':
    main()
