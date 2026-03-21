#!/bin/bash

# Stock Insight App - Start Servers Script
# Starts both frontend and backend servers with process management
# Usage: 
#   ./scripts/start.sh          # Start both servers
#   ./scripts/start.sh backend  # Start only backend
#   ./scripts/start.sh frontend # Start only frontend
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
PID_FILE="$SCRIPT_DIR/.server-pids"

# Parse arguments
SERVICE="${1:-all}"

# If specific service requested, delegate to individual script
if [ "$SERVICE" == "backend" ]; then
    exec "$SCRIPT_DIR/start-backend.sh"
elif [ "$SERVICE" == "frontend" ]; then
    exec "$SCRIPT_DIR/start-frontend.sh"
elif [ "$SERVICE" != "all" ]; then
    echo -e "${RED}❌ Invalid service: $SERVICE${NC}"
    echo "Usage: ./scripts/start.sh [all|backend|frontend]"
    exit 1
fi

echo -e "${BLUE}🚀 Starting Stock Insight App Servers${NC}"
echo "======================================"
echo ""

# Function to cleanup on error
cleanup() {
    echo -e "${RED}❌ Error occurred. Cleaning up...${NC}"
    if [ -f "$PID_FILE" ]; then
        BACKEND_PID=$(awk '{print $1}' "$PID_FILE" 2>/dev/null)
        FRONTEND_PID=$(awk '{print $2}' "$PID_FILE" 2>/dev/null)
        
        if [ ! -z "$BACKEND_PID" ] && ps -p "$BACKEND_PID" > /dev/null 2>&1; then
            kill "$BACKEND_PID" 2>/dev/null || true
        fi
        
        if [ ! -z "$FRONTEND_PID" ] && ps -p "$FRONTEND_PID" > /dev/null 2>&1; then
            kill "$FRONTEND_PID" 2>/dev/null || true
        fi
        
        rm -f "$PID_FILE"
    fi
    exit 1
}

trap cleanup ERR

# Check if servers are already running
check_port() {
    local port=$1
    if lsof -ti:$port > /dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

if check_port 8000; then
    echo -e "${YELLOW}⚠️  Port 8000 is already in use (backend may be running)${NC}"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

if check_port 3000; then
    echo -e "${YELLOW}⚠️  Port 3000 is already in use (frontend may be running)${NC}"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Start Backend Server
echo -e "${BLUE}🐍 Starting Backend Server...${NC}"
cd "$PROJECT_ROOT/backend"

# Check if virtual environment exists (venv or .venv)
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo -e "${RED}❌ Virtual environment not found. Run ./scripts/setup.sh first${NC}"
    exit 1
fi

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

# Create logs directory
mkdir -p "$PROJECT_ROOT/backend/logs"
LOG_FILE="$PROJECT_ROOT/backend/logs/backend.log"

# Start backend in background with logging (reload on any .py, .env, .toml, .ini change)
nohup uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 \
  --reload-include '*.env' --reload-include '*.toml' --reload-include '*.ini' \
  > "$LOG_FILE" 2>&1 &
BACKEND_PID=$!

# Save PID to file
echo "$BACKEND_PID" > "$SCRIPT_DIR/.backend-pid"

echo -e "${GREEN}✅ Backend server started (PID: $BACKEND_PID)${NC}"

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
    kill "$BACKEND_PID" 2>/dev/null || true
    rm -f "$SCRIPT_DIR/.backend-pid"
    exit 1
fi

echo -e "${GREEN}✅ Backend is ready${NC}"
echo ""

# Start Frontend Server
echo -e "${BLUE}⚛️  Starting Frontend Server...${NC}"
cd "$PROJECT_ROOT/frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠️  node_modules not found. Installing dependencies...${NC}"
    npm install
fi

# Create logs directory
mkdir -p "$PROJECT_ROOT/frontend/logs"
LOG_FILE="$PROJECT_ROOT/frontend/logs/frontend.log"

# Start frontend in background with logging
nohup npm run dev > "$LOG_FILE" 2>&1 &
FRONTEND_PID=$!

# Save PID to file
echo "$FRONTEND_PID" > "$SCRIPT_DIR/.frontend-pid"

echo -e "${GREEN}✅ Frontend server started (PID: $FRONTEND_PID)${NC}"

# Wait for frontend to be ready
echo "Waiting for frontend to be ready..."
FRONTEND_READY=0
for i in {1..60}; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        FRONTEND_READY=1
        break
    fi
    sleep 1
done

if [ $FRONTEND_READY -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Frontend may still be starting up${NC}"
else
    echo -e "${GREEN}✅ Frontend is ready${NC}"

    # Run error scanner once
    echo ""
    echo -e "${BLUE}🔍 Running error scanner...${NC}"
    cd "$PROJECT_ROOT/frontend"
    npm run scan:errors
    echo -e "${GREEN}✅ Scan complete. Report: frontend/error-scan-report.json${NC}"
    cd "$PROJECT_ROOT"
fi

# Save PIDs to combined file for stop.sh
if [ ! -z "$BACKEND_PID" ] && [ ! -z "$FRONTEND_PID" ]; then
    echo "$BACKEND_PID $FRONTEND_PID" > "$PID_FILE"
fi

echo ""
echo "======================================"
echo -e "${GREEN}✨ Servers Started Successfully!${NC}"
echo "======================================"
echo ""
echo "Backend:  http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "Frontend: http://localhost:3000"
echo ""
echo "To stop servers, run:"
echo "  ./scripts/stop.sh          # Stop both"
echo "  ./scripts/stop-backend.sh  # Stop backend only"
echo "  ./scripts/stop-frontend.sh # Stop frontend only"
echo ""
echo "To start individually, run:"
echo "  ./scripts/start-backend.sh  # Start backend only"
echo "  ./scripts/start-frontend.sh # Start frontend only"
echo "  ./scripts/start-celery.sh   # Start alert cron (Telegram/WhatsApp)"
echo ""
echo "PIDs saved to: $PID_FILE"
