#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./setup_kubuntu.sh </path/to/clone>

Copies the current repository to a new path (e.g., a mounted hard drive),
creates a Python 3.11 virtual environment, installs dependencies, and runs
the verification scripts you need before entering production.

You must run this on Kubuntu/Linux with sudo access so the script can install
python3.11 if it is missing.
EOF
  exit 1
}

DEST=${1:-}
if [[ -z "$DEST" ]]; then
  usage
fi

echo "==> Copying repository to ${DEST}"
mkdir -p "$DEST"
rsync -a --exclude='.venv' --exclude='dispatch.db*' --exclude='*.log' --exclude='__pycache__' . "$DEST"

cd "$DEST"

REQUIRED_PYTHON=python3.11
if ! command -v "$REQUIRED_PYTHON" > /dev/null 2>&1; then
  echo "==> Installing ${REQUIRED_PYTHON}"
  sudo apt update
  sudo apt install -y "${REQUIRED_PYTHON}" "${REQUIRED_PYTHON}-venv" "${REQUIRED_PYTHON}-distutils"
fi

echo "==> Creating virtual environment with ${REQUIRED_PYTHON}"
"${REQUIRED_PYTHON}" -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [[ ! -f .env ]]; then
  echo "==> Copying .env.example → .env (please fill in real credentials)"
  cp .env.example .env
fi

export PYTHONIOENCODING=UTF-8

echo "==> Running scenario validation (tools/test_suite.py)"
python tools/test_suite.py

echo "==> Running security regression test_component_security.py"
pytest tools/test_component_security.py

echo "==> Running Gemini smoke test (may fail without valid API key)"
if ! python tools/smoke_test_neural.py; then
  echo "⚠️ The neural smoke test failed — verify GEMINI_API_KEY and CrewAI dependencies."
fi

echo "==> Running ROI calculator for updated metrics"
python tools/roi_calculator.py

cat <<'EOF'
Setup complete. Next steps:
 1. Edit .env with the real Gemini/Twilio/Composio/dispatch credentials.
 2. Follow AUDIT_PLAYBOOK.md and the remaining audit docs (Twilio signed webhooks,
    outreach, rate-limit floods, full end-to-end run).
 3. Launch the FastAPI node: .venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8888
EOF
