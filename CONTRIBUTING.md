# Contributing to Stocky

## Prerequisites

- Docker & Docker Compose
- Node.js 20+, npm 9+
- Python 3.11+
- Git

## Quick Start

```bash
# Clone and start everything
git clone <repo>
cd stocky
cp .env.example .env        # fill in API keys
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

## Development Workflow

### Branches

```
main   ← production
test   ← staging / pre-production
dev    ← active development (default PR target)
```

Always branch off `dev`:

```bash
git checkout dev
git pull
git checkout -b feat/my-feature
```

### Running Tests

**Backend:**
```bash
cd backend
pip install -r requirements-dev.txt

# Unit tests only (fast, no DB)
pytest tests/unit -v

# All tests (needs Postgres; Redis if your tests require it — use cloud URLs or e.g.)
# docker run -d --name stocky-test-pg -e POSTGRES_PASSWORD=test -e POSTGRES_DB=stock_insight -p 5432:5432 postgres:16-alpine
pytest tests -v --cov=app --cov-fail-under=55
```

**Frontend:**
```bash
cd frontend
npm install

npm run type-check   # TypeScript
npm run lint         # ESLint
npm test             # Jest unit/component tests
npm run test:e2e     # Playwright E2E (needs running app)
```

### Code Style

**Backend** — enforced by pre-commit hooks:
- `ruff` for linting and formatting (line length 100)
- `mypy` for type checking (strict mode)

```bash
cd backend
pip install pre-commit
pre-commit install
```

**Frontend:**
- ESLint (`next/core-web-vitals`)
- Prettier (auto-format on save recommended)
- TypeScript strict mode

### Commit Messages

Use conventional commits:

```
feat: add Playwright E2E tests for portfolio flow
fix: resolve rate-limit header missing on 429
chore: bump yfinance to 0.2.55
docs: update CONTRIBUTING setup section
```

## Pull Requests

1. Target `dev` branch (not `main`)
2. CI must pass: lint, type-check, unit tests, coverage gate (55%)
3. Keep PRs focused — one feature or fix per PR
4. Add or update tests for any changed behaviour
5. Fill in the PR template (summary + test plan)

PRs targeting `test` or `main` also require integration tests and Docker image build to pass.

## AI agent rules

See **[AGENTS.md](AGENTS.md)** and [docs/ai/README.md](docs/ai/README.md) for canonical frontend/backend rules (avoid duplicating long guides in chats).

### UI/UX Pro Max (Cursor skill, optional)

Install or refresh the [ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) integration for Cursor:

```bash
npx uipro-cli@latest init --ai cursor
```

Restart Cursor after install. Full usage, `search.py` paths, and how it relates to `frontend/.cursorrules`: **[docs/ai/ui-ux-pro-max.md](docs/ai/ui-ux-pro-max.md)**.

### Superpowers (Cursor / Claude plugin, optional)

[Superpowers](https://github.com/obra/superpowers) adds agent **workflow** skills (planning, TDD, debugging, code review). It is **not** copied into this repo — install from the IDE:

```text
/add-plugin superpowers
```

(or search the marketplace for “superpowers”). See **[docs/ai/superpowers.md](docs/ai/superpowers.md)**. Git branching and PR rules in this document still win if something conflicts.

## Project Structure

```
stocky/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/   # FastAPI route handlers
│   │   ├── core/               # config, cache, database, executors
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic request/response models
│   │   ├── services/           # Business logic (stock_data, price_service, …)
│   │   └── tasks/              # Celery async tasks
│   ├── alembic/                # DB migrations
│   └── tests/
│       ├── unit/               # Pure unit tests (no DB)
│       └── integration/        # Tests against a real test DB
├── frontend/
│   ├── app/                    # Next.js App Router pages
│   ├── components/             # Shared UI + feature components
│   ├── lib/                    # API client, hooks, utilities
│   └── types/                  # TypeScript type definitions
├── docs/                       # Architecture docs, design docs
└── .github/workflows/          # CI/CD pipelines
```

## Environment Variables

See `docs/setup/ENV_SETUP.md` for the full variable reference. The minimum required for local dev:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL async URL |
| `REDIS_URL` | Redis URL |
| `SECRET_KEY` | JWT signing key |
| `OPENAI_API_KEY` | For AI analysis features |
| `ANTHROPIC_API_KEY` | For Claude agent features |

## Reporting Issues

Open a GitHub issue with:
- Steps to reproduce
- Expected vs actual behaviour
- Relevant logs or screenshots
