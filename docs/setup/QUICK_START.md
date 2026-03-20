# Quick Start - Connect Database and Run Servers

## Step 1: Fix Homebrew Permissions (if needed)

If you see permission errors, run:

```bash
sudo chown -R $(whoami) /opt/homebrew /Users/$(whoami)/Library/Logs/Homebrew
```

## Step 2: Install PostgreSQL

```bash
brew install postgresql@14
```

## Step 3: Start PostgreSQL Service

```bash
brew services start postgresql@14
```

Wait a few seconds, then verify it's running:

```bash
pg_isready
```

## Step 4: Run the App

**Option A – Local backend + frontend (recommended after DB is available):**

```bash
cd /path/to/stocky
npm run setup
# Ensure Postgres + Redis match backend/.env (e.g. steps above, or cloud URLs in .env)
npm run dev:all
```

**Option B – Full stack in Docker:**

```bash
cd /path/to/stocky
cp backend/.env.example backend/.env
# Edit backend/.env with your DATABASE_URL, REDIS_URL, CELERY_*, API keys
# Optional: cp .env.example .env  (NEXT_PUBLIC_* for the frontend container)
docker compose up --build
```

See [DOCKER.md](./DOCKER.md) for optional `docker run` snippets if you need local Postgres/Redis without Compose.

## Alternative: Manual Setup

If you prefer to set up manually, see [Run Servers](./RUN_SERVERS.md) for detailed instructions.

## After Setup

Once the servers are running:

- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000

## Troubleshooting

### PostgreSQL Not Starting

```bash
# Check if PostgreSQL is installed
brew list postgresql@14

# Check service status
brew services list | grep postgresql

# Start manually
brew services start postgresql@14

# Check if running
pg_isready
```

### Database Connection Issues

If you get connection errors, check your PostgreSQL credentials:

```bash
# Test connection
psql -U postgres -h localhost

# List databases
psql -U postgres -l
```

### Port Already in Use

If port 8000 or 3000 is already in use:

```bash
# Find process using port 8000
lsof -i :8000

# Kill process (replace PID with actual process ID)
kill -9 <PID>

# Or kill all processes on port
kill $(lsof -t -i:8000)
```

## Need Help?

See [Run Servers](./RUN_SERVERS.md) for comprehensive troubleshooting guide.
