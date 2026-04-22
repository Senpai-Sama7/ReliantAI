#!/usr/bin/env bash
# Start Ops Intelligence — backend + frontend
set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Backend ───────────────────────────────────────────────────────────────
cd "$ROOT/backend"

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "Created backend/.env from .env.example — edit as needed."
fi

if [ ! -d ".venv" ]; then
  echo "Creating backend virtualenv..."
  python3 -m venv .venv
fi

echo "Installing backend dependencies..."
.venv/bin/pip install -q -r requirements.txt

echo "Starting backend on :8095..."
.venv/bin/python main.py &
BACKEND_PID=$!

# ── Frontend ──────────────────────────────────────────────────────────────
cd "$ROOT/frontend"

if [ ! -d "node_modules" ]; then
  echo "Installing frontend dependencies..."
  npm install
fi

echo "Starting frontend on :5173..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "═══════════════════════════════════════════════"
echo " Ops Intelligence running"
echo " Backend:  http://localhost:8095"
echo " Frontend: http://localhost:5173"
echo " API docs: http://localhost:8095/docs"
echo " Health:   http://localhost:8095/health"
echo "═══════════════════════════════════════════════"
echo ""
echo "Press Ctrl+C to stop both services."

wait_and_cleanup() {
  kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
  exit 0
}
trap wait_and_cleanup INT TERM

wait
