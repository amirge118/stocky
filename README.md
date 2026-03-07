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

### Prerequisites

- Node.js 18+ and npm 9+
- Python 3.11+
- PostgreSQL 14+

### Installation

#### Option 1: Using Setup Script (Recommended)

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

#### Option 2: Manual Installation

**Frontend:**
```bash
cd frontend
npm install
```

**Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements-dev.txt
```

### Environment Setup

1. **Frontend Environment Variables**
   ```bash
   cd frontend
   cp .env.example .env.local
   # Edit .env.local with your configuration
   ```

2. **Backend Environment Variables**
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env with your configuration
   ```

### Running the Application

**Frontend:**
```bash
cd frontend
npm run dev
```
Frontend will be available at http://localhost:3000

**Backend:**
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn app.main:app --reload
```
Backend API will be available at http://localhost:8000
API documentation at http://localhost:8000/docs

## Project Structure

```
learnCursor/
├── docs/              # All documentation
│   ├── setup/        # Setup and installation guides
│   ├── testing/       # Testing documentation
│   ├── features/      # Feature completion docs
│   └── design-docs/   # Design documents
├── frontend/          # Next.js frontend application
├── backend/           # FastAPI backend application
├── .cursor/           # Cursor AI rules
│   └── rules/         # Project rules and guidelines
├── README.md          # Main project README
└── FUTURE_IMPROVEMENTS.md  # Ideas and planned features
```

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed structure guide.

## Documentation

### Setup & Installation
- **[Quick Start](docs/setup/QUICK_START.md)** - Fast setup guide
- **[Environment Setup](docs/setup/ENV_SETUP.md)** - Environment variables configuration
- **[Run Servers](docs/setup/RUN_SERVERS.md)** - Server management guide
- **[Architecture Setup](docs/setup/ARCHITECTURE_SETUP.md)** - Project architecture overview
- **[Start Development](docs/setup/START_DEVELOPMENT.md)** - Complete development setup

### Development Guides
- **[Testing Workflow](docs/testing/TESTING_WORKFLOW.md)** - Testing guide and best practices
- **[Testing Summary](docs/testing/TESTING_SUMMARY.md)** - Overview of test coverage
- **[Feature Documentation](docs/features/)** - Completed features documentation

### Project Rules & Architecture
- **Architecture**: See `.cursor/rules/architecture.md`
- **Tech Stack**: See `.cursor/rules/tech-stack-versions.md`
- **Frontend Rules**: See `frontend/.cursorrules`
- **Backend Rules**: See `backend/.cursorrules`
- **All Rules**: See `.cursor/rules/README.md`

### Planning
- **[Future Improvements](FUTURE_IMPROVEMENTS.md)** - Ideas and planned features

## Development

### Frontend Commands
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run lint` - Run ESLint
- `npm test` - Run tests
- `npm run test:e2e` - Run E2E tests

### Backend Commands
- `uvicorn app.main:app --reload` - Start development server
- `pytest` - Run tests
- `pytest --cov` - Run tests with coverage
- `black .` - Format code
- `ruff check .` - Lint code
- `mypy app` - Type check

## Contributing

See `.cursor/rules/git-workflow-rules.md` for contribution guidelines.

## License

MIT License
