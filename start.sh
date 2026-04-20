#!/bin/bash
echo "Starting AEGIS..."

# Activate virtual environment if present
if [ -d ".venv" ]; then
    . .venv/bin/activate
fi

cd backend && uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

cd frontend && npm run dev &
FRONTEND_PID=$!

function cleanup {
    echo "Stopping AEGIS..."
    kill $BACKEND_PID
    kill $FRONTEND_PID
    exit
}

trap cleanup EXIT

wait
