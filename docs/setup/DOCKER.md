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

## Troubleshooting: `500` on `/api/v1/portfolio/...` or `/alerts`

1. **Supabase + Docker + `Errno 99`** — direct host `db.*.supabase.co` is often **IPv6-only**; Docker Desktop may not reach it. Use the **pooler** URI from the Supabase dashboard (IPv4). See **[SUPABASE_DOCKER.md](./SUPABASE_DOCKER.md)**.

2. **Migrations** — the backend container runs `alembic upgrade head` on start. If it failed in older setups (errors were previously ignored), fix the DB connection and recreate the container:
   ```bash
   docker compose logs backend | tail -80
   docker compose exec backend alembic upgrade head
   docker compose restart backend
   ```
3. **`localhost:8000` in the browser Network tab** is normal when the UI calls an API on your machine; it is not wrong if your `NEXT_PUBLIC_API_BASE_URL` is `http://localhost:8000`. A **500** means the server handled the request but threw an error (often schema/DB).

4. **`OSError: [Errno 99]`** can also be **uvloop + asyncpg**; Compose runs uvicorn with **`--loop asyncio`**.

5. **Wrong `DATABASE_URL` from inside the container** or **missing TLS for cloud Postgres**. Fix:
   - Use `host.docker.internal` (not `localhost`) if Postgres runs on your Mac/host.
   - For **Supabase from Docker**, prefer the **pooler** URI (IPv4). Direct `db.*.supabase.co` is often IPv6-only → Errno 99. See [SUPABASE_DOCKER.md](./SUPABASE_DOCKER.md).
   - The app sets `ssl=True` for non-local hosts automatically (see `DATABASE_SSL` in `backend/.env.example`).
