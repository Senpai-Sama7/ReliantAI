#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PIDS_FILE="$ROOT_DIR/.pids"
LOG_DIR="$ROOT_DIR/.logs"

mkdir -p "$LOG_DIR"

echo "Starting HVAC Business Platform..."

echo "-> Starting template library (Docker)"
cd "$ROOT_DIR/hvac-template-library"
docker compose up -d
echo "   CMS: http://localhost:3000"
echo "   API: http://localhost:5000"

cd "$ROOT_DIR"

if [ -f "$PIDS_FILE" ]; then
  echo "-> Removing stale PID file"
  rm -f "$PIDS_FILE"
fi

echo "-> Starting lead generator API"
cd "$ROOT_DIR/hvac-lead-generator/api"
echo "   Building lead API..."
npm run build > "$LOG_DIR/lead-api-build.log" 2>&1
nohup node dist/server.js \
  </dev/null > "$LOG_DIR/lead-api.log" 2>&1 &
API_PID=$!
echo "$API_PID hvac-lead-generator-api" >> "$PIDS_FILE"
echo "   Lead API: http://localhost:5001 (PID: $API_PID)"

echo "-> Starting lead generator dashboard"
cd "$ROOT_DIR/hvac-lead-generator/dashboard"
echo "   Building lead dashboard..."
NODE_ENV=production npm run build > "$LOG_DIR/lead-dashboard-build.log" 2>&1
nohup ./node_modules/.bin/next start -p 3001 \
  </dev/null > "$LOG_DIR/lead-dashboard.log" 2>&1 &
DASH_PID=$!
echo "$DASH_PID hvac-lead-generator-dashboard" >> "$PIDS_FILE"
echo "   Lead Dashboard: http://localhost:3001 (PID: $DASH_PID)"

cd "$ROOT_DIR"

sleep 2

if ! kill -0 "$API_PID" >/dev/null 2>&1; then
  echo "Lead API failed to stay running. Check $LOG_DIR/lead-api.log"
  exit 1
fi

if ! kill -0 "$DASH_PID" >/dev/null 2>&1; then
  echo "Lead Dashboard failed to stay running. Check $LOG_DIR/lead-dashboard.log"
  exit 1
fi

echo
echo "All systems requested to start."
echo "Saved process IDs to $PIDS_FILE"
echo "Logs are in $LOG_DIR"
