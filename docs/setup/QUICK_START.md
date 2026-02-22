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

## Step 4: Run the Setup Script

```bash
cd /Users/amirgefen/Documents/CursorP/learnCursor
./scripts/setup-database-and-run.sh
```

The script will:
- Check PostgreSQL is running
- Prompt you for database credentials (username, password, host, port)
- Create the `stock_insight` database
- Configure backend `.env` file
- Set up Python virtual environment
- Install dependencies
- Apply database migrations
- Start both backend and frontend servers

### What to Enter When Prompted:

- **PostgreSQL username**: Usually `postgres` (or your PostgreSQL username)
- **PostgreSQL password**: Your PostgreSQL password (if you set one)
- **PostgreSQL host**: Usually `localhost` (press Enter for default)
- **PostgreSQL port**: Usually `5432` (press Enter for default)

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
