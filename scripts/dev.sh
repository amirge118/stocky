#!/bin/bash
# Start Stocky for local development
# Run from project root: ./scripts/dev.sh

set -e
cd "$(dirname "$0")/.."

echo "=== Stocky Dev Startup ==="

# Increase file limit on macOS to avoid EMFILE
if [[ "$(uname)" == "Darwin" ]]; then
  ulimit -n 10240 2>/dev/null || true
fi

# Check if backend is running
if ! curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health 2>/dev/null | grep -q 200; then
  echo ""
  echo "Backend not running. Start it in a separate terminal:"
  echo "  cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
  echo ""
  echo "Or with Docker: docker compose up backend"
  echo ""
fi

echo "Starting frontend on http://127.0.0.1:3000"
echo "Press Ctrl+C to stop"
echo ""

cd frontend && npm run dev
