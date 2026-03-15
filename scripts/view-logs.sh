#!/bin/bash

# Stock Insight App - View Server Logs
# View backend and/or frontend logs in real-time
# Usage:
#   ./scripts/view-logs.sh          # View both logs
#   ./scripts/view-logs.sh backend  # View backend logs only
#   ./scripts/view-logs.sh frontend # View frontend logs only

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

SERVICE="${1:-all}"

BACKEND_LOG="$PROJECT_ROOT/backend/logs/backend.log"
FRONTEND_LOG="$PROJECT_ROOT/frontend/logs/frontend.log"

view_backend() {
    if [ ! -f "$BACKEND_LOG" ]; then
        echo -e "${YELLOW}⚠️  Backend log file not found: $BACKEND_LOG${NC}"
        echo "Backend may not be running or hasn't generated logs yet."
        return 1
    fi
    
    echo -e "${BLUE}📋 Backend Logs (Ctrl+C to exit)${NC}"
    echo "======================================"
    echo ""
    tail -f "$BACKEND_LOG"
}

view_frontend() {
    if [ ! -f "$FRONTEND_LOG" ]; then
        echo -e "${YELLOW}⚠️  Frontend log file not found: $FRONTEND_LOG${NC}"
        echo "Frontend may not be running or hasn't generated logs yet."
        return 1
    fi
    
    echo -e "${BLUE}📋 Frontend Logs (Ctrl+C to exit)${NC}"
    echo "======================================"
    echo ""
    tail -f "$FRONTEND_LOG"
}

case "$SERVICE" in
    backend)
        view_backend
        ;;
    frontend)
        view_frontend
        ;;
    all)
        echo -e "${BLUE}📋 Viewing Both Server Logs${NC}"
        echo "======================================"
        echo ""
        echo -e "${GREEN}Tip: Use separate terminals for better experience:${NC}"
        echo "  Terminal 1: ./scripts/view-logs.sh backend"
        echo "  Terminal 2: ./scripts/view-logs.sh frontend"
        echo ""
        echo -e "${YELLOW}Showing last 20 lines of each log, then following...${NC}"
        echo ""
        
        echo -e "${BLUE}=== BACKEND LOGS (last 20 lines) ===${NC}"
        tail -20 "$BACKEND_LOG" 2>/dev/null || echo "No backend logs yet"
        echo ""
        
        echo -e "${BLUE}=== FRONTEND LOGS (last 20 lines) ===${NC}"
        tail -20 "$FRONTEND_LOG" 2>/dev/null || echo "No frontend logs yet"
        echo ""
        
        echo -e "${YELLOW}To follow logs in real-time, use:${NC}"
        echo "  tail -f $BACKEND_LOG"
        echo "  tail -f $FRONTEND_LOG"
        ;;
    *)
        echo -e "${RED}❌ Invalid service: $SERVICE${NC}"
        echo "Usage: ./scripts/view-logs.sh [all|backend|frontend]"
        exit 1
        ;;
esac
