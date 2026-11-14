#!/bin/bash
# ATLAS full-stack web app — FastAPI backend + vanilla JS frontend.
# Usage: bash webapp/run.sh [port]     (default port 8000)
set -eu
cd "$(dirname "$0")/.."
PORT="${1:-8000}"
python3 -c "import fastapi, uvicorn" 2>/dev/null || \
  pip install -r webapp/backend/requirements.txt
exec uvicorn webapp.backend.main:app --host 0.0.0.0 --port "$PORT"
