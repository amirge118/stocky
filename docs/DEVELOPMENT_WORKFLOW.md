# Development Workflow Guide

## Best Practices for Managing Start/Stop Actions

### Why Split Backend and Frontend?

**Benefits:**
1. **Faster Development** - Start only what you need
2. **Resource Efficiency** - Less CPU/memory usage
3. **Easier Debugging** - Isolated logs and processes
4. **Flexibility** - Work on one service while the other is stable
5. **Better Control** - Restart only what changed

### Development Workflow Patterns

#### Pattern 1: Backend-Only Development
**When:** Working on API endpoints, database models, business logic

```bash
# Start backend
./scripts/start-backend.sh

# Make changes, test API
curl http://localhost:8000/api/v1/health

# View logs
tail -f backend/logs/backend.log

# Stop when done
./scripts/stop-backend.sh
```

**Benefits:**
- Fast startup (~2-3 seconds)
- No frontend compilation overhead
- Direct API testing via curl/Postman/docs

#### Pattern 2: Frontend-Only Development
**When:** Working on UI components, styling, client-side logic

```bash
# Start frontend
./scripts/start-frontend.sh

# Make changes, see hot reload
# Frontend runs on http://localhost:3000

# View logs
tail -f frontend/logs/frontend.log

# Stop when done
./scripts/stop-frontend.sh
```

**Benefits:**
- Fast startup (~5-10 seconds)
- Hot module replacement (HMR)
- No backend dependency for UI work

#### Pattern 3: Full Stack Development
**When:** Testing integration, end-to-end flows, debugging communication

```bash
# Start both
./scripts/start.sh

# Or start individually
./scripts/start-backend.sh
./scripts/start-frontend.sh

# Test full application
# Backend: http://localhost:8000
# Frontend: http://localhost:3000

# Stop both
./scripts/stop.sh
```

**Benefits:**
- Complete application testing
- Verify API communication
- Test real user flows

### Process Management Best Practices

#### 1. **Use PID Files**
- Each service has its own PID file
- Easy to track running processes
- Graceful shutdown support

**Check running processes:**
```bash
# Backend PID
cat scripts/.backend-pid

# Frontend PID
cat scripts/.frontend-pid

# Both PIDs
cat scripts/.server-pids
```

#### 2. **Separate Log Files**
- Backend: `backend/logs/backend.log`
- Frontend: `frontend/logs/frontend.log`
- Easier debugging and monitoring

**Watch logs:**
```bash
# Backend logs
tail -f backend/logs/backend.log

# Frontend logs
tail -f frontend/logs/frontend.log

# Both (in separate terminals)
```

#### 3. **Port Management**
- Scripts check ports before starting
- Prompt to kill existing processes
- Fallback port checking in stop scripts

**Manual port checking:**
```bash
# Check what's on port 8000
lsof -ti:8000

# Check what's on port 3000
lsof -ti:3000

# Kill by port
lsof -ti:8000 | xargs kill -9
```

#### 4. **Graceful Shutdown**
- SIGTERM first (graceful)
- SIGKILL if needed (force)
- 5-second timeout for graceful shutdown

### Common Development Scenarios

#### Scenario 1: Quick API Test
```bash
./scripts/start-backend.sh
# Test API at http://localhost:8000/docs
./scripts/stop-backend.sh
```

#### Scenario 2: UI Component Development
```bash
./scripts/start-frontend.sh
# Edit components, see changes instantly
./scripts/stop-frontend.sh
```

#### Scenario 3: Debugging Integration Issue
```bash
# Start both with logs
./scripts/start.sh

# Terminal 1: Watch backend logs
tail -f backend/logs/backend.log

# Terminal 2: Watch frontend logs
tail -f frontend/logs/frontend.log

# Terminal 3: Test application
# Make requests, see logs in real-time
```

#### Scenario 4: Restart After Dependency Change
```bash
# Backend dependency changed
cd backend
pip install -r requirements-dev.txt
./scripts/stop-backend.sh
./scripts/start-backend.sh

# Frontend dependency changed
cd frontend
npm install
./scripts/stop-frontend.sh
./scripts/start-frontend.sh
```

### Advanced Tips

#### 1. **Alias Common Commands**
Add to your `~/.zshrc` or `~/.bashrc`:
```bash
alias sb='./scripts/start-backend.sh'
alias sf='./scripts/start-frontend.sh'
alias s='./scripts/start.sh'
alias xb='./scripts/stop-backend.sh'
alias xf='./scripts/stop-frontend.sh'
alias x='./scripts/stop.sh'
```

#### 2. **Watch Logs While Developing**
```bash
# Terminal 1: Backend logs
tail -f backend/logs/backend.log

# Terminal 2: Frontend logs  
tail -f frontend/logs/frontend.log

# Terminal 3: Development
# Make changes, see logs update
```

#### 3. **Quick Restart**
```bash
# Restart backend
./scripts/stop-backend.sh && ./scripts/start-backend.sh

# Restart frontend
./scripts/stop-frontend.sh && ./scripts/start-frontend.sh

# Restart both
./scripts/stop.sh && ./scripts/start.sh
```

#### 4. **Check Service Status**
```bash
# Check if backend is running
curl -s http://localhost:8000/api/v1/health && echo "Backend: ✅" || echo "Backend: ❌"

# Check if frontend is running
curl -s http://localhost:3000 > /dev/null && echo "Frontend: ✅" || echo "Frontend: ❌"
```

### Troubleshooting

#### Port Already in Use
```bash
# Option 1: Use stop scripts
./scripts/stop.sh

# Option 2: Kill by port
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9

# Option 3: Let script handle it
# Scripts will prompt to kill existing processes
```

#### Process Won't Stop
```bash
# Force kill by PID
kill -9 $(cat scripts/.backend-pid)
kill -9 $(cat scripts/.frontend-pid)

# Or by port
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9

# Clean up PID files
rm scripts/.backend-pid scripts/.frontend-pid scripts/.server-pids
```

#### Logs Not Appearing
```bash
# Check log file exists
ls -la backend/logs/backend.log
ls -la frontend/logs/frontend.log

# Check permissions
chmod 755 backend/logs frontend/logs

# Check disk space
df -h .
```

### Production vs Development

**Development (Current Scripts):**
- Hot reload enabled (`--reload` for backend, `npm run dev` for frontend)
- Logs to files
- PID file management
- Port checking
- Database connection verification

**Production (Future):**
- Use process managers (PM2, systemd, supervisor)
- Reverse proxy (nginx, Caddy)
- Centralized logging
- Health checks and monitoring
- Environment-specific configs

### Summary

**Quick Reference:**

| Action | Command |
|--------|---------|
| Start both | `./scripts/start.sh` |
| Start backend | `./scripts/start-backend.sh` |
| Start frontend | `./scripts/start-frontend.sh` |
| Stop both | `./scripts/stop.sh` |
| Stop backend | `./scripts/stop-backend.sh` |
| Stop frontend | `./scripts/stop-frontend.sh` |
| View backend logs | `tail -f backend/logs/backend.log` |
| View frontend logs | `tail -f frontend/logs/frontend.log` |

**Best Practice:** Start only what you need for faster development cycles!
