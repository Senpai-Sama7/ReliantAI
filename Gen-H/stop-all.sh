#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PIDS_FILE="$ROOT_DIR/.pids"

echo "Stopping HVAC Business Platform..."

echo "-> Stopping template library (Docker)"
cd "$ROOT_DIR/hvac-template-library"
docker compose down

cd "$ROOT_DIR"

if [ -f "$PIDS_FILE" ]; then
  echo "-> Stopping lead generator processes"
  while read -r pid name; do
    if [ -n "${pid:-}" ] && kill "$pid" >/dev/null 2>&1; then
      echo "   Stopped $name ($pid)"
    else
      echo "   Process already stopped: ${name:-unknown} (${pid:-n/a})"
    fi
  done < "$PIDS_FILE"
  rm -f "$PIDS_FILE"
else
  echo "-> No PID file found"
fi

echo "All services stopped."
