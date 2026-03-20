# Docker Development Workflow

## Purpose

When you add or change app services (frontend, backend, workers), keep them in the **single** [`docker-compose.yml`](../../docker-compose.yml) and document env vars in `backend/.env.example` / [`docs/setup/DOCKER.md`](../../docs/setup/DOCKER.md).

## Mandatory: Compose integration

**When creating or modifying app services** (API, Next.js, Celery workers):

1. **Add or update the service in `docker-compose.yml`** with:
   - `build` or `image` as appropriate
   - **`env_file: ./backend/.env`** for Python/Celery services (unless documented otherwise)
   - `depends_on` only between services defined in this file (no bundled `db`/`redis`)

2. **npm scripts** in root [`package.json`](../../package.json):
   - `npm run docker:up` — `docker compose up`
   - `npm run dev:backend` / `npm run dev:frontend` / `npm run dev:all` — run outside Docker

3. **Document** in Quick Start or DOCKER.md if the default flow changes.

## Recommended workflows

- **Docker:** `docker compose up --build` — URLs entirely from `backend/.env`.
- **Hybrid:** Postgres/Redis wherever you host them + `npm run dev:all` for code with hot reload.

Optional local DB/Redis: see [`docs/setup/DOCKER.md`](../../docs/setup/DOCKER.md) (`docker run` examples). You can still add a **local-only** `docker-compose.override.yml` (gitignored) if you need personal overrides.

## Example: new worker service

```yaml
# docker-compose.yml
services:
  ai-worker:
    build: ./backend
    command: python -m app.workers.ai_worker
    env_file:
      - ./backend/.env
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

## Reference

- [`docker-compose.yml`](../../docker-compose.yml)
- [`docs/setup/DOCKER.md`](../../docs/setup/DOCKER.md)
- [`package.json`](../../package.json)
