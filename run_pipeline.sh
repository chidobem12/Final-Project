#!/usr/bin/env bash
set -euo pipefail

python scripts/01_ingest.py
python scripts/02_preprocess.py
python scripts/03_train.py
python scripts/04_evaluate.py
