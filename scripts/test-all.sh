#!/bin/bash

# Stock Insight App - Comprehensive Test Runner
# Runs all tests: backend unit, backend integration, frontend unit, frontend E2E

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track test results
BACKEND_UNIT_PASSED=0
BACKEND_INTEGRATION_PASSED=0
FRONTEND_UNIT_PASSED=0
FRONTEND_E2E_PASSED=0

echo -e "${BLUE}🧪 Running All Tests${NC}"
echo "===================="
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Backend Unit Tests
echo -e "${BLUE}📦 Backend Unit Tests${NC}"
echo "-------------------"
cd "$PROJECT_ROOT/backend"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found. Run ./scripts/setup.sh first${NC}"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}❌ pytest not found. Installing dependencies...${NC}"
    pip install -r requirements-dev.txt --quiet
fi

# Run unit tests
if pytest tests/unit/ -v --tb=short; then
    BACKEND_UNIT_PASSED=1
    echo -e "${GREEN}✅ Backend unit tests passed${NC}"
else
    echo -e "${RED}❌ Backend unit tests failed${NC}"
fi
echo ""

# Backend Integration Tests
echo -e "${BLUE}🔗 Backend Integration Tests${NC}"
echo "---------------------------"
if pytest tests/integration/ -v --tb=short; then
    BACKEND_INTEGRATION_PASSED=1
    echo -e "${GREEN}✅ Backend integration tests passed${NC}"
else
    echo -e "${RED}❌ Backend integration tests failed${NC}"
fi
echo ""

# Frontend Unit Tests
echo -e "${BLUE}⚛️  Frontend Unit Tests${NC}"
echo "-------------------"
cd "$PROJECT_ROOT/frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠️  node_modules not found. Installing dependencies...${NC}"
    npm install
fi

# Run unit tests
if npm test -- --passWithNoTests; then
    FRONTEND_UNIT_PASSED=1
    echo -e "${GREEN}✅ Frontend unit tests passed${NC}"
else
    echo -e "${RED}❌ Frontend unit tests failed${NC}"
fi
echo ""

# Frontend E2E Tests
echo -e "${BLUE}🎭 Frontend E2E Tests${NC}"
echo "------------------"
if npm run test:e2e; then
    FRONTEND_E2E_PASSED=1
    echo -e "${GREEN}✅ Frontend E2E tests passed${NC}"
else
    echo -e "${RED}❌ Frontend E2E tests failed${NC}"
fi
echo ""

# Summary
echo "===================="
echo -e "${BLUE}📊 Test Summary${NC}"
echo "===================="
echo ""

if [ $BACKEND_UNIT_PASSED -eq 1 ]; then
    echo -e "Backend Unit Tests:        ${GREEN}✅ PASSED${NC}"
else
    echo -e "Backend Unit Tests:        ${RED}❌ FAILED${NC}"
fi

if [ $BACKEND_INTEGRATION_PASSED -eq 1 ]; then
    echo -e "Backend Integration Tests: ${GREEN}✅ PASSED${NC}"
else
    echo -e "Backend Integration Tests: ${RED}❌ FAILED${NC}"
fi

if [ $FRONTEND_UNIT_PASSED -eq 1 ]; then
    echo -e "Frontend Unit Tests:        ${GREEN}✅ PASSED${NC}"
else
    echo -e "Frontend Unit Tests:        ${RED}❌ FAILED${NC}"
fi

if [ $FRONTEND_E2E_PASSED -eq 1 ]; then
    echo -e "Frontend E2E Tests:         ${GREEN}✅ PASSED${NC}"
else
    echo -e "Frontend E2E Tests:         ${RED}❌ FAILED${NC}"
fi

echo ""

# Exit with error if any test suite failed
if [ $BACKEND_UNIT_PASSED -eq 0 ] || [ $BACKEND_INTEGRATION_PASSED -eq 0 ] || [ $FRONTEND_UNIT_PASSED -eq 0 ] || [ $FRONTEND_E2E_PASSED -eq 0 ]; then
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
else
    echo -e "${GREEN}✨ All tests passed!${NC}"
    exit 0
fi
