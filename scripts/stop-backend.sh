#!/bin/bash

# Stock Insight App - Stop Backend Server
# Stops only the backend server gracefully

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PID_FILE="$SCRIPT_DIR/.backend-pid"

echo -e "${BLUE}🛑 Stopping Backend Server${NC}"
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

# Read PID from file if it exists
if [ -f "$PID_FILE" ]; then
    BACKEND_PID=$(cat "$PID_FILE" 2>/dev/null)
    
    if [ ! -z "$BACKEND_PID" ]; then
        kill_process "$BACKEND_PID" "Backend"
    fi
    
    # Remove PID file
    rm -f "$PID_FILE"
    echo -e "${GREEN}✅ PID file removed${NC}"
else
    echo -e "${YELLOW}⚠️  PID file not found. Checking port 8000...${NC}"
fi

# Fallback: Check port directly
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

check_and_kill_port 8000 "Backend"

echo ""
echo "======================================"
echo -e "${GREEN}✨ Backend Server Stopped${NC}"
echo "======================================"
