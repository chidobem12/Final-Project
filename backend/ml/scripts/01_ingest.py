from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd

from config import DATA_RAW_DIR, RAW_COMBINED_PATH, TARGET_COLUMN
from scripts.common import clean_dataframe, ensure_parent, find_csv_files
from src.data_ingestion import report_shape


def ingest_raw_files(raw_dir: Path = DATA_RAW_DIR, output_path: Path = RAW_COMBINED_PATH) -> pd.DataFrame:
    csv_files = find_csv_files(raw_dir)
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {raw_dir}")

    combined_frames = []
    for csv_path in csv_files:
        df = pd.read_csv(csv_path, low_memory=False)
        df.columns = df.columns.str.strip()

        if TARGET_COLUMN not in df.columns:
            raise ValueError(f"Missing target column '{TARGET_COLUMN}' in file: {csv_path.name}")

        print(f"Loaded {csv_path.name}: {len(df):,} rows")
        combined_frames.append(df)

    combined = pd.concat(combined_frames, ignore_index=True)
    combined = clean_dataframe(combined)

    ensure_parent(output_path)
    combined.to_csv(output_path, index=False)
    report_shape(combined, name=str(output_path))
    return combined


if __name__ == "__main__":
    ingest_raw_files()
