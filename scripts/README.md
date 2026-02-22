# Development Scripts

This directory contains scripts to manage the Stock Insight application during development.

## Quick Start

### Start Both Servers
```bash
./scripts/start.sh
```

### Stop Both Servers
```bash
./scripts/stop.sh
```

## Individual Service Management

### Backend Only

**Start Backend:**
```bash
./scripts/start-backend.sh
```

**Stop Backend:**
```bash
./scripts/stop-backend.sh
```

**View Backend Logs:**
```bash
tail -f backend/logs/backend.log
```

### Frontend Only

**Start Frontend:**
```bash
./scripts/start-frontend.sh
```

**Stop Frontend:**
```bash
./scripts/stop-frontend.sh
```

**View Frontend Logs:**
```bash
tail -f frontend/logs/frontend.log
```

## Advanced Usage

### Start Specific Service
```bash
./scripts/start.sh backend   # Start only backend
./scripts/start.sh frontend  # Start only frontend
./scripts/start.sh          # Start both (default)
```

### Stop Specific Service
```bash
./scripts/stop.sh backend   # Stop only backend
./scripts/stop.sh frontend  # Stop only frontend
./scripts/stop.sh          # Stop both (default)
```

## Development Workflow Best Practices

### 1. **Separate Development**
When working on only backend or frontend:
- Start only the service you're working on
- Faster startup time
- Less resource usage
- Easier debugging

**Example:**
```bash
# Working on backend API
./scripts/start-backend.sh
# Make changes, test API at http://localhost:8000/docs
./scripts/stop-backend.sh
```

### 2. **Full Stack Development**
When testing integration:
- Start both services
- Test full user flows
- Verify API communication

**Example:**
```bash
./scripts/start.sh
# Test full application
./scripts/stop.sh
```

### 3. **Process Management**

**Check Running Processes:**
```bash
# Check backend
lsof -ti:8000

# Check frontend
lsof -ti:3000

# Check both
ps aux | grep -E "(uvicorn|next)"
```

**View Process IDs:**
```bash
cat scripts/.backend-pid
cat scripts/.frontend-pid
cat scripts/.server-pids
```

### 4. **Logging**

All scripts write logs to separate files:
- Backend: `backend/logs/backend.log`
- Frontend: `frontend/logs/frontend.log`

**Watch logs in real-time:**
```bash
# Backend logs
tail -f backend/logs/backend.log

# Frontend logs
tail -f frontend/logs/frontend.log

# Both logs (in separate terminals)
```

### 5. **Port Conflicts**

If ports are already in use:
- Scripts will prompt to kill existing processes
- Or manually kill: `lsof -ti:8000 | xargs kill -9`
- Or use: `./scripts/stop.sh` first

### 6. **Database Requirements**

Backend requires PostgreSQL:
- Scripts verify database connection before starting
- If connection fails, check:
  - PostgreSQL is running: `brew services list | grep postgresql`
  - Database exists: `psql -U postgres -lqt | grep stock_insight`
  - Credentials in `backend/.env`

## Script Files

| Script | Purpose | PID File | Log File |
|--------|---------|----------|----------|
| `start.sh` | Start both servers | `.server-pids` | N/A (delegates) |
| `stop.sh` | Stop both servers | `.server-pids` | N/A (delegates) |
| `start-backend.sh` | Start backend only | `.backend-pid` | `backend/logs/backend.log` |
| `stop-backend.sh` | Stop backend only | `.backend-pid` | N/A |
| `start-frontend.sh` | Start frontend only | `.frontend-pid` | `frontend/logs/frontend.log` |
| `stop-frontend.sh` | Stop frontend only | `.frontend-pid` | N/A |
| `test-all.sh` | Run all tests | N/A | N/A |
| `setup-database-and-run.sh` | Setup DB and start | N/A | N/A |

## Troubleshooting

### Backend won't start
1. Check database connection: `./scripts/start-backend.sh`
2. Verify PostgreSQL is running
3. Check `backend/logs/backend.log` for errors
4. Verify `backend/.env` configuration

### Frontend won't start
1. Check `frontend/logs/frontend.log` for errors
2. Verify `node_modules` exists: `cd frontend && npm install`
3. Check port 3000 is free: `lsof -ti:3000`

### Port already in use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Or use stop scripts
./scripts/stop.sh
```

### Processes not stopping
```bash
# Force kill by port
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9

# Remove PID files
rm scripts/.backend-pid scripts/.frontend-pid scripts/.server-pids
```

## Production Considerations

For production deployment:
- Use process managers (PM2, systemd, supervisor)
- Use reverse proxy (nginx, Caddy)
- Separate log management
- Environment-specific configurations
- Health checks and monitoring

These scripts are designed for **development only**.
