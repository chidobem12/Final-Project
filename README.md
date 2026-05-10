# AEGIS v2 — SOC Threat Operations Platform

AEGIS is a full-stack cybersecurity operations platform with:
- FastAPI backend (REST + WebSocket threat stream)
- React + Vite frontend (live dashboard, feed, analytics, map)
- Ensemble ML predictions (logistic regression, random forest, gradient boosting)
- Built-in traffic simulator for continuous demo data

## Requirements

- Python 3.11+
- Node.js 20+
- pnpm 8+

## Local Setup (Recommended)

1) Clone and enter project
```bash
git clone <your-repo-url>
cd cyber-threat
```

2) Create Python environment and install backend dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install .
```

3) Install frontend dependencies
```bash
pnpm -C frontend install
```

4) Run backend (Terminal 1)
```bash
source .venv/bin/activate
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

5) Run frontend (Terminal 2)
```bash
pnpm -C frontend dev --host 0.0.0.0 --port 5173
```

6) Open app
- Frontend: http://localhost:5173
- Backend API docs: http://localhost:8000/docs

## Login Credentials (Prototype)

- Analyst
	- Email: `analyst@keystone.bank`
	- Password: `aegis2026`
- Admin
	- Email: `admin@keystone.bank`
	- Password: `aegisadmin`

## Docker Setup

From repository root:
```bash
docker-compose up --build
```

Then open http://localhost:5173.

## ML Pipeline

Run the full ML pipeline (ingest → preprocess → train → evaluate):
```bash
bash run_pipeline.sh
```

Train on individual datasets:
```bash
python scripts/train_kdd.py     # KDD Cup 99
python scripts/train_unsw.py    # UNSW-NB15
```

Cross-dataset evaluation:
```bash
python scripts/cross_dataset_eval.py
```

### Project Structure
```
src/                    # Modular ML library
  data_ingestion.py     # Load & validate CSVs
  preprocessing.py      # Clean, encode, normalise, SMOTE, split
  models.py             # LR / RF / GBM training + GridSearchCV
  evaluation.py         # Metrics, confusion matrices, feature importance
scripts/                # Pipeline scripts
  common.py             # Shared utilities
  01_ingest.py          # Load raw CSVs → combined dataset
  02_preprocess.py      # Clean → encode → select features → split → SMOTE
  03_train.py           # Train 3 models with GridSearchCV
  04_evaluate.py        # Evaluate metrics, confusion matrices, feature importance
  05_predict.py         # CLI inference on new CSV
  train_kdd.py          # Train on KDD Cup 99
  train_unsw.py         # Train on UNSW-NB15
  cross_dataset_eval.py # Cross-dataset validation
models/                 # Trained model artifacts
backend/                # FastAPI backend
frontend/               # React + Vite frontend
```

## Quick Verification

Backend tests:
```bash
source .venv/bin/activate
python -m pytest backend/tests -q
```

All tests:
```bash
python -m pytest tests/ -v
```

Frontend build:
```bash
pnpm -C frontend build
```

## Key Runtime Endpoints

- WebSocket threat stream: `ws://localhost:8000/ws/threats`
- Auth: `POST /api/auth/login`, `GET /api/auth/me`, `POST /api/auth/logout`
- Metrics: `GET /api/metrics`
- Simulator: `POST /api/simulate/attack`, `POST /api/simulate/stop`

## Notes

- The simulator runs continuously after backend startup and feeds live events.
- Model files are loaded from the `models/` directory.
- `outputs/figures/` assets are mirrored to `frontend/public/figures/` for Analytics visuals.
