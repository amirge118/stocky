# CLAUDE.md — Stocky Stock Insight App

> Canonical rules for Claude Code. Read this first on every session.
> Full rule index: [`docs/ai/README.md`](docs/ai/README.md)

## Quick Start

```bash
# Backend (FastAPI on :8000)
cd backend && uvicorn app.main:app --reload

# Frontend (Next.js on :3000)
cd frontend && npm run dev

# Run all backend tests
cd backend && pytest

# Run all frontend tests
cd frontend && npm test

# Run E2E tests
cd frontend && npm run test:e2e
```

## Architecture in One Paragraph

Frontend (Next.js 15 App Router) talks to Backend (FastAPI) via JSON REST under `/api/v1/`. Frontend has zero business logic and zero direct DB access. Backend layers: HTTP router → Pydantic schemas → Services → Models/DB/external APIs. Stock data comes from `yfinance`. AI analysis uses Anthropic Claude via `anthropic` SDK.

## Non-Obvious Gotchas (Read Before Writing Code)

### 1. Mandatory Request/Response Logging (backend)
Every new backend API endpoint MUST be covered by the logging middleware. Reference: `backend/app/middleware/request_logging.py`. Redacts: `password`, `token`, `secret`, `api_key`, `authorization`. Log level: INFO for 2xx/3xx, WARNING for 4xx, ERROR for 5xx.

### 2. FUTURE_IMPROVEMENTS.md is Mandatory
For every feature request, improvement idea, or "nice to have" identified during implementation: add it to `FUTURE_IMPROVEMENTS.md` at the repo root. Use `- [ ] Description [PRIORITY]`. Never skip this.

### 3. Async SQLAlchemy 2.0 Patterns
Use `select()` (not `query()`). Use `AsyncSession` injected via `Depends(get_db_session)`. Use `selectinload`/`joinedload` for eager loading. **Test DB uses `sqlite+aiosqlite:///:memory:`** — do NOT assume PostgreSQL in tests. See `backend/tests/conftest.py` for fixture pattern.

### 4. TanStack Query v5 Patterns
Use `isPending` for loading skeletons (NOT `isLoading` — that's v4). Get query client via `useQueryClient()` hook (NOT a singleton import). On mutation success: `invalidateQueries`. On mutation error: `toast({ variant: "destructive" })`.

### 5. No Direct `fetch` in Components
Use `get`/`post`/`put`/`del` from `@/lib/api/client.ts`. Never call `fetch()` directly from components or hooks.

### 6. Finance Number Formatting
- Currency: `toLocaleString("en-US", { style: "currency", currency: "USD" })`
- Percentages: `${n >= 0 ? "+" : ""}${n.toFixed(2)}%`
- Prices: `font-mono` class; numeric tables: `tabular-nums`
- Gain: `text-green-400` / `bg-green-400/10`. Loss: `text-red-400` / `bg-red-400/10`

## Key File Map

| What you need | Where |
|---|---|
| Frontend conventions, API client, dark theme tokens | `frontend/.cursorrules` |
| Backend conventions, DB patterns, structure | `backend/.cursorrules` |
| REST conventions, error codes, logging spec | `.cursor/rules/api-design-rules.md` |
| Testing pyramid (70/20/10), fixtures, patterns | `.cursor/rules/testing-rules.md` |
| Git branching, commit format | `.cursor/rules/git-workflow-rules.md` |
| All AI rules (full index) | `docs/ai/README.md` |

## Directory Conventions

```
frontend/
  app/                      # Next.js App Router pages (keep thin)
  components/features/      # Domain components (stocks/, portfolio/, market/, watchlist/)
  components/ui/            # Shadcn primitives (never hand-roll)
  lib/api/                  # API client functions (client.ts is the base)
  lib/hooks/                # Custom React hooks
  types/                    # TypeScript interfaces for API responses

backend/
  app/api/v1/endpoints/     # FastAPI routers
  app/services/             # Business logic (stock_service.py, yfinance_service.py, etc.)
  app/schemas/              # Pydantic request/response models
  app/models/               # SQLAlchemy models
  app/middleware/           # request_logging.py, error_handler.py
  tests/unit/               # pytest unit tests (mock external deps)
  tests/integration/        # pytest integration tests (test API endpoints)
```

## Dark Theme Tokens

| Token | Use |
|---|---|
| `bg-zinc-950` | Page canvas |
| `bg-zinc-900` | Cards, panels |
| `bg-zinc-800` | Table headers, hover, inputs |
| `border-zinc-800` | Card borders |
| `text-zinc-400` | Secondary / labels |
| `text-green-400` / `text-red-400` | Gain / loss |
| `bg-green-400/10` / `bg-red-400/10` | Gain / loss badge backgrounds |

Card pattern: `rounded-xl border border-zinc-800 bg-zinc-900`

## Testing Requirements

- Backend: pytest, 80%+ coverage, `@pytest.mark.asyncio`, mock yfinance and external APIs.
- Frontend: Jest + React Testing Library, test loading/error/success states. Playwright for E2E.
- Pyramid: 70% unit / 20% integration / 10% E2E.
- Never mark a feature complete without tests.

## Commit Format

```
<type>(<scope>): <subject>
```
Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `ci`
Example: `feat(stocks): add dividend history endpoint`
