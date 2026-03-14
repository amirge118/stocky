# Docker Development Workflow

## Purpose

This rule ensures that when you add or modify services (frontend, backend, AI agents, databases, caches, etc.), they are properly integrated into Docker and npm scripts so developers can run the app with minimal setup.

## Mandatory: Add New Services to Docker

**When creating or modifying ANY of the following:**

- Backend API (FastAPI, Flask, etc.)
- Frontend app (Next.js, React, etc.)
- AI/ML services (agents, workers, inference)
- Databases (PostgreSQL, Redis, etc.)
- Message queues, caches, or other infrastructure

**You MUST:**

1. **Add the service to `docker-compose.yml`** with:
   - Appropriate `build` or `image`
   - Environment variables (from `.env.example`)
   - Health checks where applicable
   - Correct `depends_on` for startup order

2. **Add npm scripts to root `package.json`** for common workflows:
   - `npm run docker:infra` – runs only infrastructure (db, redis) for local dev
   - `npm run docker:up` – runs full stack
   - `npm run dev:backend` / `npm run dev:frontend` – run app services locally with hot reload

3. **Document in README** how to start the new service (Option A/B/C as in Quick Start)

## Recommended Development Workflow

**Option A (preferred):** Docker for infra, local for code

- Terminal 1: `npm run docker:infra` (db, redis)
- Terminal 2: `npm run dev:all` (backend + frontend with hot reload)

**Option B:** Full Docker

- `npm run docker:up` – everything in containers
- Use `docker-compose.override.yml` for volume mounts and `--reload` when developing

## Adding a New Service – Checklist

1. Add service block to `docker-compose.yml`
2. Add to `docker:infra` profile or create `docker:app` if it's an app service
3. Add `npm run dev:<service>` to `package.json` if it runs locally
4. Update `backend/.env.example` (or relevant `.env.example`) with connection details for localhost when using `docker:infra`
5. Update README Quick Start if the default flow changes

## Example: Adding a New AI Worker

```yaml
# docker-compose.yml
services:
  ai-worker:
    build: ./backend
    command: python -m app.workers.ai_worker
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    depends_on:
      db: { condition: service_healthy }
      redis: { condition: service_healthy }
```

```json
// package.json
"dev:worker": "cd backend && ./venv/bin/python -m app.workers.ai_worker"
```

## Reference

- Root [package.json](../../package.json) – npm scripts
- [docker-compose.yml](../../docker-compose.yml) – service definitions
- [README.md](../../README.md) – Quick Start and commands
