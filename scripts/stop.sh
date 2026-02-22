#!/bin/bash

# Stock Insight App - Stop Servers Script
# Stops all running servers gracefully using stored PIDs
# Usage:
#   ./scripts/stop.sh          # Stop both servers
#   ./scripts/stop.sh backend  # Stop only backend
#   ./scripts/stop.sh frontend # Stop only frontend

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PID_FILE="$SCRIPT_DIR/.server-pids"

# Parse arguments
SERVICE="${1:-all}"

# If specific service requested, delegate to individual script
if [ "$SERVICE" == "backend" ]; then
    exec "$SCRIPT_DIR/stop-backend.sh"
elif [ "$SERVICE" == "frontend" ]; then
    exec "$SCRIPT_DIR/stop-frontend.sh"
elif [ "$SERVICE" != "all" ]; then
    echo -e "${RED}❌ Invalid service: $SERVICE${NC}"
    echo "Usage: ./scripts/stop.sh [all|backend|frontend]"
    exit 1
fi

echo -e "${BLUE}🛑 Stopping Stock Insight App Servers${NC}"
echo "======================================"
echo ""

# Function to kill process gracefully
kill_process() {
    local pid=$1
    local name=$2
    
    if [ -z "$pid" ] || ! ps -p "$pid" > /dev/null 2>&1; then
        return 0  # Process doesn't exist
    fi
    
    echo -e "${YELLOW}Stopping $name (PID: $pid)...${NC}"
    
    # Try graceful shutdown (SIGTERM)
    kill "$pid" 2>/dev/null || true
    
    # Wait up to 5 seconds for graceful shutdown
    for i in {1..5}; do
        if ! ps -p "$pid" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $name stopped gracefully${NC}"
            return 0
        fi
        sleep 1
    done
    
    # Force kill if still running
    if ps -p "$pid" > /dev/null 2>&1; then
        echo -e "${YELLOW}Force killing $name...${NC}"
        kill -9 "$pid" 2>/dev/null || true
        sleep 1
        if ! ps -p "$pid" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $name stopped${NC}"
        else
            echo -e "${RED}❌ Failed to stop $name${NC}"
            return 1
        fi
    fi
    
    return 0
}

# Read PIDs from file if it exists
if [ -f "$PID_FILE" ]; then
    BACKEND_PID=$(awk '{print $1}' "$PID_FILE" 2>/dev/null)
    FRONTEND_PID=$(awk '{print $2}' "$PID_FILE" 2>/dev/null)
    
    # Also check individual PID files
    if [ -z "$BACKEND_PID" ] && [ -f "$SCRIPT_DIR/.backend-pid" ]; then
        BACKEND_PID=$(cat "$SCRIPT_DIR/.backend-pid" 2>/dev/null)
    fi
    if [ -z "$FRONTEND_PID" ] && [ -f "$SCRIPT_DIR/.frontend-pid" ]; then
        FRONTEND_PID=$(cat "$SCRIPT_DIR/.frontend-pid" 2>/dev/null)
    fi
    
    if [ ! -z "$BACKEND_PID" ]; then
        kill_process "$BACKEND_PID" "Backend"
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill_process "$FRONTEND_PID" "Frontend"
    fi
    
    # Remove PID files
    rm -f "$PID_FILE" "$SCRIPT_DIR/.backend-pid" "$SCRIPT_DIR/.frontend-pid"
    echo -e "${GREEN}✅ PID files removed${NC}"
else
    echo -e "${YELLOW}⚠️  Combined PID file not found. Checking individual PID files...${NC}"
    
    # Try individual scripts
    if [ -f "$SCRIPT_DIR/.backend-pid" ]; then
        "$SCRIPT_DIR/stop-backend.sh" || true
    fi
    
    if [ -f "$SCRIPT_DIR/.frontend-pid" ]; then
        "$SCRIPT_DIR/stop-frontend.sh" || true
    fi
fi

# Fallback: Check ports directly
check_and_kill_port() {
    local port=$1
    local name=$2
    
    local pid=$(lsof -ti:$port 2>/dev/null | head -1)
    if [ ! -z "$pid" ]; then
        echo -e "${YELLOW}Found $name process on port $port (PID: $pid)${NC}"
        kill_process "$pid" "$name"
    else
        echo -e "${GREEN}✅ No $name process found on port $port${NC}"
    fi
}

echo ""
echo "Checking ports directly..."
check_and_kill_port 8000 "Backend"
check_and_kill_port 3000 "Frontend"

echo ""
echo "======================================"
echo -e "${GREEN}✨ Servers Stopped${NC}"
echo "======================================"
