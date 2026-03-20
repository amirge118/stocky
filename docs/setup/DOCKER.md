# Docker

There is a **single** Compose file: [`docker-compose.yml`](../../docker-compose.yml) — **backend**, **Celery worker**, **Celery beat**, **frontend**.

## Configure

1. **`backend/.env`** (required) — copy from `backend/.env.example` and set:
   - `DATABASE_URL`, `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`
   - `SECRET_KEY`, `CORS_ORIGINS`, API keys, etc.

2. **Repo root `.env`** (optional) — for `NEXT_PUBLIC_API_BASE_URL` / `NEXT_PUBLIC_APP_ENV` when running the frontend container (see root `.env.example`). Defaults work for local API at `http://localhost:8000`.

## Run

```bash
docker compose up --build
```

Or: `npm run docker:up`

No Postgres/Redis services are defined in Compose — use whatever URLs you put in `backend/.env` (managed cloud, or processes you start yourself).

## Optional: local Postgres / Redis without extra compose files

Examples if you need a quick local database for development or integration tests:

```bash
# PostgreSQL (adjust user/password/db to match backend/.env)
docker run -d --name stocky-pg -e POSTGRES_USER=stocky -e POSTGRES_PASSWORD=stocky_dev \
  -e POSTGRES_DB=stock_insight -p 5432:5432 postgres:16-alpine

# Redis
docker run -d --name stocky-redis -p 6379:6379 redis:7-alpine
```

Then point `backend/.env` at `localhost` (or `host.docker.internal` from **inside** app containers if the DB runs on the host).

## Containers and the host

`docker-compose.yml` sets `extra_hosts: host.docker.internal:host-gateway` on Python services so `DATABASE_URL` can use `host.docker.internal` when the DB listens on your machine, not inside Compose.
