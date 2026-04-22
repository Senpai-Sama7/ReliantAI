#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# Setup script for the local‑first AI platform.
# This script builds all container images defined in the compose file.
# Usage: ./setup.sh
# -----------------------------------------------------------------------------

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "[INFO] Building docker images..."
docker compose -f "$SCRIPT_DIR/compose.yaml" build --parallel 1
echo "[INFO] Build complete. You can now run ./run_end_to_end.sh"
