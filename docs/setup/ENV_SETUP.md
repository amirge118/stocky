# Environment Variables Setup Guide

This guide explains how to set up environment variables for the Stock Insight App.

## Quick Setup

### Frontend

1. Copy the example file:
   ```bash
   cd frontend
   cp .env.example .env.local
   ```

2. Edit `.env.local` with your values:
   ```bash
   # Required
   NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
   NEXT_PUBLIC_APP_ENV=development
   ```

### Backend

1. Copy the example file:
   ```bash
   cd backend
   cp .env.example .env
   ```

2. Edit `.env` with your values (see details below)

## Frontend Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_BASE_URL` | Backend API base URL | `http://localhost:8000` |
| `NEXT_PUBLIC_APP_ENV` | Application environment | `development`, `production`, `staging` |

**Note**: Variables prefixed with `NEXT_PUBLIC_` are exposed to the browser. Never put sensitive data in these variables.

## Backend Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://user:pass@localhost:5432/dbname` |
| `SECRET_KEY` | JWT secret key (generate secure random string) | See [Generating Secret Key](#generating-secret-key) |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiration time | `30` |
| `OPENAI_API_KEY` | OpenAI API key | Get from [OpenAI Platform](https://platform.openai.com/api-keys) |
| `ANTHROPIC_API_KEY` | Anthropic API key | Get from [Anthropic Console](https://console.anthropic.com/) |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | `http://localhost:3000` |

### Optional Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection string (for caching) | `redis://localhost:6379/0` |
| `ENVIRONMENT` | Application environment | `development`, `production`, `staging` |
| `LOG_LEVEL` | Logging level | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |

## Generating Secret Key

For production, generate a secure random secret key:

### Using OpenSSL
```bash
openssl rand -hex 32
```

### Using Python
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Using Node.js
```bash
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

## Database Setup

### PostgreSQL Connection String Format

```
postgresql+asyncpg://username:password@host:port/database
```

### Example for Local Development

```bash
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/stock_insight
```

### Cloud Postgres (Supabase, Neon, RDS) + Docker

`asyncpg` needs **TLS** for most remote hosts. The backend enables `ssl=True` automatically when the URL host is **not** `localhost`, `127.0.0.1`, `host.docker.internal`, or common Compose service names (`postgres`, `db`, `database`).

- **`DATABASE_SSL=true`** — force SSL (optional; same as default for remote hosts).
- **`DATABASE_SSL=false`** — disable SSL if your DB is reachable on a “remote” hostname but does not use TLS (unusual).

From **app containers**, point `DATABASE_URL` at `host.docker.internal` (or your cloud URL), not `localhost`, if the database listens on the host machine.

If you see **`OSError: [Errno 99] Cannot assign requested address`**, check URL, TLS, and IPv4 vs IPv6 for your provider.

If you see **`SSLCertVerificationError`** / *self signed certificate in certificate chain* when using **macOS Command Line Tools Python** (LibreSSL) or a **corporate proxy**, set **`DATABASE_SSL_VERIFY=false`** in `backend/.env` for **local development only** (never in production). Prefer a Python build linked to OpenSSL (e.g. `brew install python@3.11`) or fix system trust store instead.

### Creating Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE stock_insight;

# Create user (optional)
CREATE USER stock_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE stock_insight TO stock_user;
```

## API Keys Setup

### OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Navigate to API Keys section
4. Click "Create new secret key"
5. Copy the key and add it to `.env`:
   ```
   OPENAI_API_KEY=sk-...
   ```

### Anthropic API Key

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Sign in or create an account
3. Navigate to API Keys section
4. Click "Create Key"
5. Copy the key and add it to `.env`:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```

## CORS Configuration

For development, allow localhost:
```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

For production, specify your domain:
```bash
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

## Environment-Specific Configurations

### Development
```bash
ENVIRONMENT=development
LOG_LEVEL=DEBUG
CORS_ORIGINS=http://localhost:3000
```

### Production
```bash
ENVIRONMENT=production
LOG_LEVEL=INFO
CORS_ORIGINS=https://yourdomain.com
SECRET_KEY=<generate-secure-random-key>
```

## Security Best Practices

1. **Never commit `.env` files** - They are gitignored for a reason
2. **Use strong secret keys** - Generate random keys for production
3. **Rotate keys regularly** - Change API keys and secrets periodically
4. **Use different keys per environment** - Don't reuse production keys in development
5. **Limit CORS origins** - Only allow trusted domains
6. **Use environment variables** - Never hardcode secrets in code

## Troubleshooting

### Frontend can't connect to backend
- Check `NEXT_PUBLIC_API_BASE_URL` matches backend URL
- Ensure backend is running
- Check CORS configuration in backend

### Backend database connection fails
- Verify PostgreSQL is running: `pg_isready`
- Check `DATABASE_URL` format is correct
- Ensure database exists and user has permissions

### API keys not working
- Verify keys are correct (no extra spaces)
- Check API key permissions in provider dashboard
- Ensure you have sufficient credits/quota

## Verification

After setting up environment variables, verify they're loaded:

### Frontend
```bash
cd frontend
npm run dev
# Check browser console for API_BASE_URL
```

### Backend
```bash
cd backend
source venv/bin/activate
python -c "from app.core.config import settings; print(settings.database_url)"
```

## Next Steps

After setting up environment variables:

1. **Run database migrations**:
   ```bash
   cd backend
   alembic upgrade head
   ```

2. **Start development servers**:
   ```bash
   # Terminal 1: Backend
   cd backend && uvicorn app.main:app --reload
   
   # Terminal 2: Frontend
   cd frontend && npm run dev
   ```

3. **Verify setup**:
   - Backend: http://localhost:8000/docs
   - Frontend: http://localhost:3000
