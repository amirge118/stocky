#!/bin/bash

# Stock Insight App - Start Backend Server
# Starts only the backend server
# Usage: ./scripts/start-backend.sh

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
PID_FILE="$SCRIPT_DIR/.backend-pid"
LOG_FILE="$SCRIPT_DIR/../backend/logs/backend.log"

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/backend/logs"

echo -e "${BLUE}🐍 Starting Backend Server${NC}"
echo "======================================"
echo ""

# Function to cleanup on error
cleanup() {
    echo -e "${RED}❌ Error occurred. Cleaning up...${NC}"
    if [ -f "$PID_FILE" ]; then
        BACKEND_PID=$(cat "$PID_FILE" 2>/dev/null)
        if [ ! -z "$BACKEND_PID" ] && ps -p "$BACKEND_PID" > /dev/null 2>&1; then
            kill "$BACKEND_PID" 2>/dev/null || true
        fi
        rm -f "$PID_FILE"
    fi
    exit 1
}

trap cleanup ERR

# Check if backend is already running
check_port() {
    local port=$1
    if lsof -ti:$port > /dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

if check_port 8000; then
    echo -e "${YELLOW}⚠️  Port 8000 is already in use${NC}"
    if [ -t 0 ]; then
        # Interactive mode
        read -p "Kill existing process and start new one? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        # Non-interactive mode - auto-kill
        echo -e "${YELLOW}Non-interactive mode: Killing existing process...${NC}"
    fi
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

cd "$PROJECT_ROOT/backend"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found. Run ./scripts/setup.sh first${NC}"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Verify database connection before starting backend
echo -e "${BLUE}🔍 Verifying database connection...${NC}"
python3 << EOF
import asyncio
import asyncpg
import sys
from app.core.config import settings

async def test_connection():
    try:
        db_url = settings.database_url.replace('postgresql+asyncpg://', 'postgresql://')
        conn = await asyncpg.connect(db_url, timeout=5)
        await conn.execute('SELECT 1')
        await conn.close()
        print("✅ Database connection verified")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {type(e).__name__}: {e}")
        if "Connect call failed" in str(e) or "connection refused" in str(e).lower():
            print("   → PostgreSQL may not be running")
            print("   → Start PostgreSQL: brew services start postgresql@14")
        elif "authentication failed" in str(e).lower():
            print("   → Database credentials may be incorrect")
            print("   → Check backend/.env file")
        elif "does not exist" in str(e).lower() or "database" in str(e).lower():
            print("   → Database may not exist")
            print("   → Run: ./scripts/setup-database-and-run.sh")
        else:
            print(f"   → Database URL: {settings.database_url[:60]}...")
        return False

result = asyncio.run(test_connection())
sys.exit(0 if result else 1)
EOF

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Cannot start backend: Database connection failed${NC}"
    echo ""
    echo "Please fix the database connection issue and try again."
    exit 1
fi
echo ""

# Check if dependencies are installed
if ! python -c "import uvicorn" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Dependencies not installed. Installing...${NC}"
    pip install -r requirements-dev.txt --quiet
fi

# Start backend in background with logging
echo -e "${BLUE}🚀 Starting uvicorn server...${NC}"
nohup uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 > "$LOG_FILE" 2>&1 &
BACKEND_PID=$!

# Save PID to file
echo "$BACKEND_PID" > "$PID_FILE"

echo -e "${GREEN}✅ Backend server started (PID: $BACKEND_PID)${NC}"
echo -e "${BLUE}📝 Logs: $LOG_FILE${NC}"

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
BACKEND_READY=0
for i in {1..30}; do
    if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        BACKEND_READY=1
        break
    fi
    sleep 1
done

if [ $BACKEND_READY -eq 0 ]; then
    echo -e "${RED}❌ Backend server failed to start${NC}"
    echo -e "${YELLOW}Check logs: $LOG_FILE${NC}"
    kill "$BACKEND_PID" 2>/dev/null || true
    rm -f "$PID_FILE"
    exit 1
fi

echo ""
echo "======================================"
echo -e "${GREEN}✨ Backend Server Started Successfully!${NC}"
echo "======================================"
echo ""
echo "Backend:  http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "Logs:     $LOG_FILE"
echo ""
echo "To stop backend, run:"
echo "  ./scripts/stop-backend.sh"
echo ""
echo "PID saved to: $PID_FILE"
echo ""
echo -e "${BLUE}💡 Tip: Use 'tail -f $LOG_FILE' to watch logs${NC}"
