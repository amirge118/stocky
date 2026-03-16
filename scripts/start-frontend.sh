#!/bin/bash

# Stock Insight App - Start Frontend Server
# Starts only the frontend server
# Usage: ./scripts/start-frontend.sh

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
PID_FILE="$SCRIPT_DIR/.frontend-pid"
LOG_FILE="$SCRIPT_DIR/../frontend/logs/frontend.log"

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/frontend/logs"

echo -e "${BLUE}⚛️  Starting Frontend Server${NC}"
echo "======================================"
echo ""

# Function to cleanup on error
cleanup() {
    echo -e "${RED}❌ Error occurred. Cleaning up...${NC}"
    if [ -f "$PID_FILE" ]; then
        FRONTEND_PID=$(cat "$PID_FILE" 2>/dev/null)
        if [ ! -z "$FRONTEND_PID" ] && ps -p "$FRONTEND_PID" > /dev/null 2>&1; then
            kill "$FRONTEND_PID" 2>/dev/null || true
        fi
        rm -f "$PID_FILE"
    fi
    exit 1
}

trap cleanup ERR

# Check if frontend is already running
check_port() {
    local port=$1
    if lsof -ti:$port > /dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

if check_port 3000; then
    echo -e "${YELLOW}⚠️  Port 3000 is already in use${NC}"
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
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

cd "$PROJECT_ROOT/frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠️  node_modules not found. Installing dependencies...${NC}"
    npm install
fi

# Increase file descriptor limit to prevent EMFILE errors
# macOS default is often 256, which can be too low for Next.js file watching
ulimit -n 4096 2>/dev/null || true

# Start frontend in background with logging
echo -e "${BLUE}🚀 Starting Next.js dev server...${NC}"
# Set NODE_OPTIONS to reduce file watcher load
# Don't specify host - let Next.js use default (avoids permission issues)
NODE_OPTIONS="--max-old-space-size=4096" nohup npm run dev > "$LOG_FILE" 2>&1 &
FRONTEND_PID=$!

# Save PID to file
echo "$FRONTEND_PID" > "$PID_FILE"

echo -e "${GREEN}✅ Frontend server started (PID: $FRONTEND_PID)${NC}"
echo -e "${BLUE}📝 Logs: $LOG_FILE${NC}"

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
    echo -e "${YELLOW}Check logs: $LOG_FILE${NC}"
else
    echo -e "${GREEN}✅ Frontend is ready${NC}"
fi

echo ""
echo "======================================"
echo -e "${GREEN}✨ Frontend Server Started Successfully!${NC}"
echo "======================================"
echo ""
echo "Frontend: http://localhost:3000"
echo "Logs:     $LOG_FILE"
echo ""
echo "To stop frontend, run:"
echo "  ./scripts/stop-frontend.sh"
echo ""
echo "PID saved to: $PID_FILE"
echo ""
echo -e "${BLUE}💡 Tip: Use 'tail -f $LOG_FILE' to watch logs${NC}"
