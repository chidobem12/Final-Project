# AEGIS v2 — SOC Threat Operations Platform

AEGIS is a full-stack cybersecurity operations platform with real-time threat detection, ensemble ML predictions, and a live simulation environment.

- **Backend:** FastAPI (REST + WebSocket) with ensemble ML inference
- **Frontend:** React + Vite + TypeScript with live SOC dashboard
- **ML Pipeline:** Logistic Regression, Random Forest, Gradient Boosting with GridSearchCV + SMOTE
- **Simulator:** Built-in traffic generator for continuous demo data

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AEGIS Platform                            │
│                                                             │
│  ┌─────────────┐    WebSocket    ┌──────────────────────┐   │
│  │   Frontend   │◄──────────────►│     Backend           │   │
│  │  (React +     │    REST API   │   (FastAPI + Uvicorn) │   │
│  │   Vite)       │               │                       │   │
│  │  Port 5173    │               │  ┌─────────────────┐  │   │
│  └─────────────┘                │  │  ML Ensemble     │  │   │
│                                 │  │  (LR / RF / GBM) │  │   │
│  ┌─────────────┐                │  └─────────────────┘  │   │
│  │  Simulator   │──────────────►│  ┌─────────────────┐  │   │
│  │ (10 events/s)│  events loop  │  │  Simulator       │  │   │
│  └─────────────┘                │  │  (5 scenarios)   │  │   │
│                      Port 8000  │  └─────────────────┘  │   │
│                      Port 8000  └──────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Requirements

- **Python** 3.11+
- **Node.js** 20+
- **pnpm** 8+ (or npm)
- **uv** (recommended) or pip

## Quick Start

### 1. Clone and enter the project

```bash
git clone <your-repo-url>
cd Final-Project
```

### 2. Backend setup

Create a Python virtual environment and install dependencies:

```bash
# Using uv (recommended)
uv sync

# OR using pip
python -m venv .venv
source .venv/bin/activate
pip install .
```

### 3. Frontend setup

```bash
pnpm -C frontend install
```

### 4. Run the application

**Option A — Two terminals:**

Terminal 1 — Backend:
```bash
source .venv/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Terminal 2 — Frontend:
```bash
pnpm -C frontend dev --host 0.0.0.0 --port 5173
```

**Option B — Single script:**
```bash
bash start.sh
```

### 5. Open the app

- **Frontend:** http://localhost:5173
- **Backend API docs:** http://localhost:8000/docs
- **WebSocket endpoint:** `ws://localhost:8000/ws/threats`

## Docker Setup

From repository root:

```bash
docker-compose up --build
```

This builds and starts both the backend (port 8000) and frontend (port 5173).

## Login Credentials (Prototype)

| Role | Email | Password |
|------|-------|----------|
| Analyst | `analyst@keystone.bank` | `aegis2026` |
| Admin | `admin@keystone.bank` | `aegisadmin` |

## ML Pipeline

### Full pipeline (ingest → preprocess → train → evaluate)

From the `backend/ml/` directory:

```bash
source .venv/bin/activate
cd backend/ml
bash run_pipeline.sh
```

This runs:
1. **01_ingest.py** — Load raw CSVs from `data/raw/`, validate, combine → `data/processed/raw_combined.csv`
2. **02_preprocess.py** — Clean, label-encode, train/test split (80/20, stratified), `StandardScaler`, `SelectKBest` (k=30), `SMOTE` oversampling → train/test CSVs + `scaler.joblib` + `selected_features.json`
3. **03_train.py** — Train 3 models with `GridSearchCV` (3-fold):
   - Logistic Regression (C: [0.1, 1.0], solver: lbfgs)
   - Random Forest (n_estimators: [50, 100], max_depth: [10, 20])
   - Gradient Boosting (learning_rate: 0.1, n_estimators: 50, max_depth: 3)
4. **04_evaluate.py** — Per-model metrics (accuracy, precision, recall, F1, ROC-AUC), confusion matrices, feature importance plots

Outputs are saved to:
- `models/` — `.joblib` model files, scaler, selected features
- `outputs/metrics/` — `metrics_summary.json`, `best_model.json`
- `outputs/figures/` — Confusion matrix PNGs, feature importance plots

### Train on individual datasets

```bash
python scripts/train_kdd.py     # KDD Cup 99
python scripts/train_unsw.py    # UNSW-NB15
```

### Cross-dataset evaluation

Evaluate CICIDS2017-trained models against KDD Cup 99 and UNSW-NB15:

```bash
python scripts/cross_dataset_eval.py
```

### CLI inference

Run predictions on a new CSV file:

```bash
python scripts/05_predict.py input.csv [--model random_forest]
```

## API Endpoints

### Authentication

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/login` | Authenticate and receive JWT |
| GET | `/api/auth/me` | Get current user info |
| POST | `/api/auth/logout` | Revoke JWT token |

### Simulation control

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/simulate/attack` | Trigger attack scenario (body: `{"scenario_id": "ddos_flood"}`) |
| POST | `/api/simulate/stop` | Stop active scenario |
| POST | `/api/simulate/pause` | Pause simulation |
| POST | `/api/simulate/resume` | Resume simulation |

### Data & metrics

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/metrics` | System metrics (events/min, threat rate, etc.) |
| GET | `/api/events?limit=100` | Recent threat events |
| GET | `/api/stats` | System stats alias |
| GET | `/api/debug/test-scenarios` | Run all 12 attack types and report detection rates |

### WebSocket

| Path | Direction | Description |
|------|-----------|-------------|
| `/ws/threats` | Server → Client | Real-time `threat_event` and `stats_update` messages |

## Attack Scenarios

| ID | Name | Type | Duration | Events/s |
|----|------|------|----------|----------|
| `ddos_flood` | DDoS Flood Attack | DDoS | 30s | 50 |
| `ransomware_outbreak` | Ransomware Lateral Movement | Infiltration | 45s | 20 |
| `apt_intrusion` | Advanced Persistent Threat | Infiltration | 60s | 2 |
| `credential_stuffing` | Credential Stuffing Campaign | Brute Force | 20s | 30 |
| `insider_exfiltration` | Insider Data Exfiltration | Exfiltration | 25s | 5 |

Trigger via: `POST /api/simulate/attack` with body `{"scenario_id": "<id>"}`.

## Frontend

### Tech stack
- **Framework:** React 18 + TypeScript
- **Bundler:** Vite 5
- **Styling:** Tailwind CSS 3 (custom SOC-themed design system)
- **State:** Zustand (single store)
- **Charts:** Recharts + D3
- **Routing:** React Router DOM 6
- **Real-time:** Native WebSocket with auto-reconnect (5 attempts, 3s interval)
- **Testing:** Vitest (unit) + Playwright (E2E)

### Frontend scripts

| Script | Command |
|--------|---------|
| `dev` | `pnpm dev` (or `npm run dev`) |
| `build` | `pnpm build` |
| `lint` | `pnpm lint` |
| `test` | `pnpm test` (Vitest) |
| `test:e2e` | `pnpm test:e2e` (Playwright) |

### Pages

- **Dashboard** — Live metrics, threat chart, model agreement, recent alerts
- **Threat Feed** — Real-time event stream with filtering
- **Threat Map** — Network topology visualization
- **Analytics** — Model performance metrics and training evaluation figures
- **Settings** — Sound alerts toggle, data export (CSV/JSON)

## Project Structure

```
.
├── backend/
│   ├── main.py                     # FastAPI app entry point
│   ├── api/
│   │   ├── routes.py               # REST + WebSocket endpoints
│   │   └── ws_handler.py           # WebSocket ConnectionManager
│   ├── auth/
│   │   ├── models.py               # Auth Pydantic schemas
│   │   ├── router.py               # Login/me/logout routes
│   │   └── utils.py                # JWT + password hashing
│   ├── data/
│   │   ├── event_store.py          # In-memory event ring buffer (10k)
│   │   └── stats_aggregator.py     # Real-time stats tracker
│   ├── ml/
│   │   ├── config.py               # Centralized ML paths
│   │   ├── model_loader.py         # ModelManager (load .joblib)
│   │   ├── predictor.py            # Ensemble inference
│   │   ├── run_pipeline.sh         # ML pipeline orchestrator
│   │   ├── data/raw/               # Raw CSV datasets
│   │   ├── data/processed/         # Preprocessed train/test CSVs
│   │   ├── models/                 # Trained .joblib artifacts
│   │   ├── outputs/                # Metrics + figures
│   │   ├── scripts/                # Pipeline scripts (01-05)
│   │   │   ├── 01_ingest.py
│   │   │   ├── 02_preprocess.py
│   │   │   ├── 03_train.py
│   │   │   ├── 04_evaluate.py
│   │   │   ├── 05_predict.py
│   │   │   ├── train_kdd.py
│   │   │   ├── train_unsw.py
│   │   │   └── cross_dataset_eval.py
│   │   ├── src/                    # ML library modules
│   │   │   ├── data_ingestion.py
│   │   │   ├── preprocessing.py
│   │   │   ├── models.py
│   │   │   └── evaluation.py
│   │   └── tests/                  # ML unit tests
│   ├── simulator/
│   │   ├── network_simulator.py    # Async event generator
│   │   ├── packet_generator.py     # Feature generation
│   │   └── attack_scenarios.py     # Scenario definitions
│   ├── tests/                      # Backend API tests
│   ├── Dockerfile
│   └── __init__.py
├── frontend/
│   ├── src/
│   │   ├── main.tsx                # React entry point
│   │   ├── App.tsx                 # Router + layout
│   │   ├── pages/                  # Dashboard, Feed, Map, Analytics, Settings, Login
│   │   ├── components/
│   │   │   ├── dashboard/          # MetricCard, LiveThreatChart, etc.
│   │   │   ├── layout/             # AppLayout, Sidebar, TopBar
│   │   │   └── shared/             # ProtectedRoute, ErrorBoundary
│   │   ├── hooks/                  # useWebSocket
│   │   ├── store/                  # useAegisStore (Zustand)
│   │   └── lib/                    # api, audioAlerts, formatters
│   ├── public/figures/             # Mirrored ML evaluation figures
│   ├── tests/                      # E2E tests
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   └── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── start.sh
└── README.md
```

## Testing

### Backend tests

```bash
source .venv/bin/activate
python -m pytest backend/tests -q
```

### ML pipeline tests

```bash
python -m pytest backend/ml/tests -v
```

### All Python tests

```bash
python -m pytest tests/ -v
```

### Frontend tests

```bash
pnpm -C frontend test          # Unit tests (Vitest)
pnpm -C frontend test:e2e     # E2E tests (Playwright)
```

### Frontend build verification

```bash
pnpm -C frontend build
```

## Runtime Behavior

- **Simulator** starts automatically on backend boot, generating ~10 events/sec
- **ML models** are loaded from `backend/ml/models/` on startup
- **Events** flow: simulator → ML predictor → event store → stats aggregator → WebSocket broadcast
- **Authentication** is JWT-based (HS256, 24h expiry) with two hardcoded users
- **Output figures** in `backend/ml/outputs/figures/` are mirrored to `frontend/public/figures/` for the Analytics page

## Notes

- The simulator runs continuously after backend startup and feeds live events.
- All data is in-memory — restarting the server clears events and state.
- Model files are loaded from the `models/` directory.
- `backend/ml/outputs/figures/` assets are mirrored to `frontend/public/figures/` for Analytics visuals.
- The `uv.lock` file is managed by `uv`; `pip` users should delete it.
