# Run Servers Guide

## Quick Start

### Option 1: Automated Script (Recommended)

```bash
chmod +x scripts/setup-database-and-run.sh
./scripts/setup-database-and-run.sh
```

This script will:
1. Check PostgreSQL installation
2. Create the database
3. Configure environment variables
4. Apply migrations
5. Start both servers

### Option 2: Manual Setup

## Step-by-Step Manual Setup

### 1. Install PostgreSQL (if not installed)

**macOS:**
```bash
brew install postgresql@14
brew services start postgresql@14
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install postgresql-14 postgresql-contrib
sudo systemctl start postgresql
```

**Windows:**
Download and install from: https://www.postgresql.org/download/windows/

### 2. Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE stock_insight;

# Verify
\l

# Exit
\q
```

### 3. Configure Backend

**Update `backend/.env`:**
```bash
cd backend
cp .env.example .env
# Edit .env with your database credentials
```

**Key settings:**
```env
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/stock_insight
SECRET_KEY=<generate with: openssl rand -hex 32>
```

### 4. Set Up Backend

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements-dev.txt

# Apply migrations
alembic upgrade head
```

### 5. Start Backend Server

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Start server
uvicorn app.main:app --reload
```

Backend will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health

### 6. Configure Frontend

```bash
cd frontend
cp .env.example .env.local
# .env.local should have: NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### 7. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 8. Start Frontend Server

```bash
cd frontend
npm run dev
```

Frontend will be available at: http://localhost:3000

## Running Both Servers

You need **two terminal windows**:

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

## Verify Everything Works

1. **Backend Health Check:**
   ```bash
   curl http://localhost:8000/api/v1/health
   ```
   Should return: `{"status":"healthy","timestamp":"...","version":"v1"}`

2. **Backend API Docs:**
   Open browser: http://localhost:8000/docs

3. **Frontend:**
   Open browser: http://localhost:3000

4. **Test Stock API:**
   ```bash
   # Create a stock
   curl -X POST http://localhost:8000/api/v1/stocks \
     -H "Content-Type: application/json" \
     -d '{
       "symbol": "AAPL",
       "name": "Apple Inc.",
       "exchange": "NASDAQ",
       "sector": "Technology"
     }'
   
   # Get stocks
   curl http://localhost:8000/api/v1/stocks
   ```

## Troubleshooting

### PostgreSQL Connection Issues

**Check PostgreSQL is running:**
```bash
pg_isready
# or
brew services list  # macOS
sudo systemctl status postgresql  # Linux
```

**Test connection:**
```bash
psql -U postgres -h localhost -d stock_insight
```

**Common issues:**
- Wrong password in DATABASE_URL
- PostgreSQL not running
- Wrong port (default is 5432)
- Database doesn't exist

### Backend Won't Start

**Check virtual environment:**
```bash
which python  # Should show venv path
```

**Check dependencies:**
```bash
pip list | grep fastapi
pip list | grep sqlalchemy
```

**Check .env file:**
```bash
cat backend/.env | grep DATABASE_URL
```

**Common errors:**
- Database connection failed → Check DATABASE_URL
- Module not found → Run `pip install -r requirements-dev.txt`
- Port 8000 in use → Change port or kill process using port

### Frontend Won't Start

**Check Node.js version:**
```bash
node --version  # Should be 18+
```

**Check dependencies:**
```bash
ls node_modules  # Should exist
```

**Common errors:**
- Port 3000 in use → Change port or kill process
- Module not found → Run `npm install`
- API connection failed → Check backend is running and CORS is configured

### Migration Issues

**Check migration status:**
```bash
cd backend
source venv/bin/activate
alembic current
```

**Reset migrations (if needed):**
```bash
# WARNING: This will drop all tables
alembic downgrade base
alembic upgrade head
```

**Create new migration:**
```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Database Connection String Examples

**Local default:**
```
postgresql+asyncpg://postgres:postgres@localhost:5432/stock_insight
```

**Custom user:**
```
postgresql+asyncpg://myuser:mypassword@localhost:5432/stock_insight
```

**Remote database:**
```
postgresql+asyncpg://user:pass@remote-host:5432/stock_insight
```

## Quick Commands Reference

```bash
# Start PostgreSQL (macOS)
brew services start postgresql@14

# Create database
createdb -U postgres stock_insight

# Backend
cd backend && source venv/bin/activate && uvicorn app.main:app --reload

# Frontend  
cd frontend && npm run dev

# Check processes
lsof -i :8000  # Backend
lsof -i :3000  # Frontend

# Stop processes
kill $(lsof -t -i:8000)  # Backend
kill $(lsof -t -i:3000)  # Frontend
```
