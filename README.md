# Stocky

Stocky is a full-stack AI-powered stock analysis platform. It lets you browse and track stocks, manage a portfolio with sector allocation analysis, and run AI agents that automatically generate deep-dive reports on individual stocks, portfolio health, market opportunities, and sector trends.

## What the App Does

### Stock Browser
Search and view any stock with live market data pulled from Yahoo Finance (price, volume, P/E ratio, market cap, 52-week range, and more). Each stock has a dedicated detail page with key financial metrics.

### Portfolio Tracker
Add holdings to your portfolio and get a real-time sector breakdown showing allocation percentages across sectors (Technology, Healthcare, Finance, etc.) with both a visual chart and a summary table.

### AI Agent System
Four background AI agents run on a schedule and can also be triggered manually:

- **Stock Deep Dive** — Comprehensive AI analysis of a specific stock: fundamentals, sentiment, risks, and a buy/hold/sell recommendation.
- **Portfolio Health** — Reviews your portfolio for diversification, concentration risk, and overall balance, with actionable rebalancing suggestions.
- **Market Scanner** — Scans the broader market for momentum, volatility signals, and emerging opportunities.
- **Sector Trend** — Analyzes performance trends across market sectors and highlights which sectors are strengthening or weakening.

All agents store their results in the database and cache the latest report in Redis for fast retrieval. The `/agents` dashboard shows the status and latest output of every agent; clicking through shows full report history.

### API
Full REST API documented at `/docs` (Swagger UI). All data is accessible programmatically.

## Tech Stack

- **Frontend**: Next.js 15.1.0, React 19.0.0, TypeScript 5.3.3, Tailwind CSS 3.4.1
- **Backend**: FastAPI 0.109.0, Python 3.11+, SQLAlchemy 2.0.25, Pydantic 2.5.3
- **Database**: PostgreSQL (with asyncpg)
- **AI Services**: OpenAI, Anthropic

## Quick Start

### Option A: Docker infra + local code (recommended for development)

Hot reload, fast iteration, logs in terminal.

**Terminal 1 – start PostgreSQL + Redis:**
```bash
npm run docker:infra
# or: docker-compose up db redis
```

**Terminal 2 – start backend + frontend:**
```bash
npm run setup          # first time only
npm run dev:all
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

Backend expects `DATABASE_URL` and `REDIS_URL` pointing to localhost (see `backend/.env.example`). Use `stocky:stocky_dev@localhost:5432/stock_insight` and `redis://localhost:6379/0` when infra runs via Docker.

### Option B: Full Docker

```bash
docker-compose up
```

All services in containers. No local venv/node needed. For backend hot reload, copy `docker-compose.override.yml.example` to `docker-compose.override.yml`.

### Option C: Run by service

```bash
npm run dev:backend   # backend only (requires db + redis)
npm run dev:frontend  # frontend only (requires backend on :8000)
npm run dev          # frontend only (alias)
```

### Commands reference

| Command | Description |
|--------|-------------|
| `npm run setup` | Install frontend + backend deps |
| `npm run dev:all` | Backend + frontend (concurrently) |
| `npm run docker:infra` | Start db + redis only |
| `npm run docker:up` | Full stack in Docker |
| `npm run test:all` | Run backend + frontend tests |

### Troubleshooting

| Error | Solution |
|-------|----------|
| `uv_interface_addresses` / crash on start | Fixed in `npm run dev` (uses `--hostname 127.0.0.1`). Update frontend if you have an old version. |
| `EMFILE: too many open files` | Run `ulimit -n 10240` before starting, or add to `~/.zshrc` |
| Port 3000 in use | App will use 3001. Open http://localhost:3001 |
| "Failed to connect to server" | Ensure backend is running on port 8000 |
