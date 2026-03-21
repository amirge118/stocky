#!/bin/bash
# Stock Insight App - Start Celery Worker + Beat Scheduler
# Runs the background alert checker every 60 seconds.
# Usage: ./scripts/start-celery.sh

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo -e "${BLUE}🔔 Starting Celery Worker + Beat Scheduler${NC}"
echo "Polls active alerts every 60s and fires Telegram/WhatsApp notifications."
echo ""

cd "$PROJECT_ROOT/backend"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo -e "${RED}❌ Virtual environment not found. Run pip install -r requirements.txt first.${NC}"
    exit 1
fi

echo -e "${BLUE}Starting worker (Ctrl+C to stop)...${NC}"
echo ""

# --beat runs the scheduler in the same process (dev-friendly; use separate celery beat in prod)
exec celery -A app.celery_app worker --beat --loglevel=info --concurrency=2
