"""Tests for ingestion pipeline behavior."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_column_validation(tmp_path: Path):
    script = load_module(Path("scripts/01_ingest.py"), "ingest_script")

    raw_dir = tmp_path / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    bad_file = raw_dir / "bad.csv"
    pd.DataFrame({"f1": [1, 2], "f2": [3, 4]}).to_csv(bad_file, index=False)

    with pytest.raises(ValueError):
        script.ingest_raw_files(raw_dir=raw_dir, output_path=tmp_path / "combined.csv")


def test_multi_file_concat(tmp_path: Path):
    script = load_module(Path("scripts/01_ingest.py"), "ingest_script_concat")

    raw_dir = tmp_path / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    pd.DataFrame({"feat": [1, 2], "Label": ["BENIGN", "ATTACK"]}).to_csv(raw_dir / "a.csv", index=False)
    pd.DataFrame({"feat": [3], "Label": ["BENIGN"]}).to_csv(raw_dir / "b.csv", index=False)

    output_path = tmp_path / "combined.csv"
    combined = script.ingest_raw_files(raw_dir=raw_dir, output_path=output_path)

    assert output_path.exists()
    assert len(combined) == 3
