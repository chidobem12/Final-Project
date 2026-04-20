# AEGIS v2 — SOC Threat Operations Platform

AEGIS is a full-stack cybersecurity operations platform with:
- FastAPI backend (REST + WebSocket threat stream)
- React + Vite frontend (live dashboard, feed, incidents, analytics, map)
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
pip install -r requirements.txt
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

## Quick Verification

Backend tests:
```bash
source .venv/bin/activate
python -m pytest backend/tests -q
```

Frontend build:
```bash
pnpm -C frontend build
```

## Key Runtime Endpoints

- WebSocket threat stream: `ws://localhost:8000/ws/threats`
- Auth: `POST /api/auth/login`, `GET /api/auth/me`, `POST /api/auth/logout`
- Incidents: `GET/POST /api/incidents`, `PATCH /api/incidents/{id}`
- Metrics: `GET /api/metrics`
- Simulator: `POST /api/simulate/attack`, `POST /api/simulate/stop`

## Notes

- The simulator runs continuously after backend startup and feeds live events.
- Model files are loaded from the `models/` directory.
- `outputs/figures/` assets are mirrored to `frontend/public/figures/` for Analytics visuals.
