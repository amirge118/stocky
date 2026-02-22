#!/bin/bash

# Stock Insight App - Database Setup and Server Startup Script

set -e  # Exit on error

# Get script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo "🚀 Setting up database and starting servers..."
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo -e "${YELLOW}⚠️  PostgreSQL not found in PATH${NC}"
    echo ""
    echo "Please install PostgreSQL first:"
    echo "  macOS: brew install postgresql@14"
    echo "  Linux: sudo apt-get install postgresql-14"
    echo "  Or download from: https://www.postgresql.org/download/"
    echo ""
    read -p "Press Enter after installing PostgreSQL, or Ctrl+C to exit..."
fi

# Check if PostgreSQL is running
if ! pg_isready &> /dev/null; then
    echo -e "${YELLOW}⚠️  PostgreSQL is not running${NC}"
    echo ""
    echo "Starting PostgreSQL..."
    
    # Try to start PostgreSQL (macOS with Homebrew)
    if command -v brew &> /dev/null; then
        brew services start postgresql@14 2>/dev/null || brew services start postgresql 2>/dev/null || true
        sleep 2
    fi
    
    # Check again
    if ! pg_isready &> /dev/null; then
        echo -e "${RED}❌ Could not start PostgreSQL automatically${NC}"
        echo "Please start PostgreSQL manually:"
        echo "  macOS: brew services start postgresql@14"
        echo "  Linux: sudo systemctl start postgresql"
        exit 1
    fi
fi

echo -e "${GREEN}✅ PostgreSQL is running${NC}"
echo ""

# Get database credentials
echo "Database Setup"
echo "=============="
read -p "PostgreSQL username [postgres]: " DB_USER
DB_USER=${DB_USER:-postgres}

read -sp "PostgreSQL password: " DB_PASSWORD
echo ""

read -p "PostgreSQL host [localhost]: " DB_HOST
DB_HOST=${DB_HOST:-localhost}

read -p "PostgreSQL port [5432]: " DB_PORT
DB_PORT=${DB_PORT:-5432}

DB_NAME="stock_insight"

# Create database connection string
DATABASE_URL="postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

echo ""
echo "Creating database..."

# Create database (using psql)
export PGPASSWORD="${DB_PASSWORD}"
if psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -lqt | cut -d \| -f 1 | grep -qw "${DB_NAME}"; then
    echo -e "${YELLOW}⚠️  Database '${DB_NAME}' already exists${NC}"
    read -p "Do you want to drop and recreate it? (y/N): " RECREATE
    if [[ $RECREATE =~ ^[Yy]$ ]]; then
        psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -c "DROP DATABASE ${DB_NAME};"
        psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -c "CREATE DATABASE ${DB_NAME};"
        echo -e "${GREEN}✅ Database recreated${NC}"
    else
        echo "Using existing database"
    fi
else
    psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -c "CREATE DATABASE ${DB_NAME};"
    echo -e "${GREEN}✅ Database created${NC}"
fi
unset PGPASSWORD

echo ""

# Update backend .env file
echo "Updating backend .env file..."
cd "$PROJECT_ROOT/backend"

if [ ! -f ".env" ]; then
    cp .env.example .env
fi

# Update DATABASE_URL in .env
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s|DATABASE_URL=.*|DATABASE_URL=${DATABASE_URL}|" .env
else
    # Linux
    sed -i "s|DATABASE_URL=.*|DATABASE_URL=${DATABASE_URL}|" .env
fi

# Generate SECRET_KEY if not already set
if grep -q "SECRET_KEY=your-secret-key-change-this-in-production" .env; then
    SECRET_KEY=$(openssl rand -hex 32)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY}|" .env
    else
        sed -i "s|SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY}|" .env
    fi
    echo -e "${GREEN}✅ Generated SECRET_KEY${NC}"
fi

echo -e "${GREEN}✅ Backend .env configured${NC}"
echo ""

# Set up Python virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing/updating dependencies..."
pip install --upgrade pip --quiet
pip install -r requirements-dev.txt --quiet

echo -e "${GREEN}✅ Backend dependencies installed${NC}"
echo ""

# Verify database connection before proceeding
echo "Verifying database connection..."
cd "$PROJECT_ROOT/backend"
source venv/bin/activate

# Test database connection
python3 << EOF
import asyncio
import asyncpg
import sys
from app.core.config import settings

async def test_connection():
    try:
        # Extract connection details from DATABASE_URL
        db_url = settings.database_url.replace('postgresql+asyncpg://', 'postgresql://')
        conn = await asyncpg.connect(db_url)
        await conn.execute('SELECT 1')
        await conn.close()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {type(e).__name__}: {e}")
        print(f"   Database URL: {settings.database_url[:50]}...")
        return False

result = asyncio.run(test_connection())
sys.exit(0 if result else 1)
EOF

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Database connection verification failed${NC}"
    echo ""
    echo "Please check:"
    echo "  1. PostgreSQL is running: brew services start postgresql@14"
    echo "  2. Database credentials in backend/.env are correct"
    echo "  3. Database 'stock_insight' exists"
    exit 1
fi

echo ""

# Apply database migrations
echo "Applying database migrations..."
alembic upgrade head
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Database migrations failed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Migrations applied${NC}"
echo ""

# Start backend server in background
echo "Starting backend server..."
echo "Backend will be available at: http://localhost:8000"
echo "API docs will be available at: http://localhost:8000/docs"
echo ""

uvicorn app.main:app --reload &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Check if backend started successfully
if ps -p $BACKEND_PID > /dev/null; then
    echo -e "${GREEN}✅ Backend server started (PID: $BACKEND_PID)${NC}"
else
    echo -e "${RED}❌ Backend server failed to start${NC}"
    exit 1
fi

echo ""

# Frontend setup
cd ../frontend

echo "Setting up frontend..."

# Check if .env.local exists
if [ ! -f ".env.local" ]; then
    cp .env.example .env.local
    echo -e "${GREEN}✅ Frontend .env.local created${NC}"
fi

# Install frontend dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
    echo -e "${GREEN}✅ Frontend dependencies installed${NC}"
fi

echo ""
echo "Starting frontend server..."
echo "Frontend will be available at: http://localhost:3000"
echo ""

npm run dev &
FRONTEND_PID=$!

# Wait a moment for frontend to start
sleep 3

# Check if frontend started successfully
if ps -p $FRONTEND_PID > /dev/null; then
    echo -e "${GREEN}✅ Frontend server started (PID: $FRONTEND_PID)${NC}"
else
    echo -e "${RED}❌ Frontend server failed to start${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✨ Setup complete!${NC}"
echo ""
echo "Servers are running:"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "  Frontend: http://localhost:3000"
echo ""
echo "To stop servers, press Ctrl+C or run:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo ""

# Wait for user interrupt
wait
