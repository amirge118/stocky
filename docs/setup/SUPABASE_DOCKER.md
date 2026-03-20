# Supabase + Docker (macOS / Docker Desktop)

## Symptom

- `GET /api/v1/health` shows `database: error` with **`OSError: [Errno 99] Cannot assign requested address`**, or
- Backend container exits during `alembic upgrade head` with the same error.

## Cause

The **direct** host `db.<project-ref>.supabase.co` often resolves to **IPv6 only** (no IPv4 `A` record). Many Docker Desktop setups **cannot open a working TCP path** to that IPv6 address, so the connection fails before Postgres answers.

This is **not** a wrong password and **not** fixed by `DATABASE_SSL_VERIFY` alone.

## Fix (recommended)

Use Supabase’s **Connection pooler** — the pooler hostname has **IPv4**.

The backend **does not** rewrite pooler hostnames to raw IPs (connecting by IP to the pooler can break auth and look like `InvalidPasswordError`).

1. Open **Supabase Dashboard** → your project → **Project Settings** → **Database**.
2. Under **Connection string**, choose **URI** and switch the mode to **Session pooler** (best for FastAPI / long-lived connections) or **Transaction pooler** (port **6543**).
3. Copy the URI and adapt it for this app:
   - Scheme: **`postgresql+asyncpg://`** (not `postgresql://`).
   - Keep user, password, host, port, and database as shown.
4. **Transaction pooler (port 6543)** with SQLAlchemy/asyncpg: append to the URL:

   `?prepared_statement_cache_size=0`

   Example shape:

   `postgresql+asyncpg://postgres.xxxx:PASSWORD@aws-0-REGION.pooler.supabase.com:6543/postgres?prepared_statement_cache_size=0`

5. Put the result in **`backend/.env`** as `DATABASE_URL`, then:

   ```bash
   docker compose up -d --build --force-recreate backend
   ```

## Still stuck?

- Confirm from the host: `docker compose run --rm --no-deps backend python -c "import socket; print(socket.getaddrinfo('YOUR_POOLER_HOST', 5432, socket.AF_INET, socket.SOCK_STREAM)[0][4][0])"` — should print an IPv4 address.
- Enable **IPv6** in Docker Desktop *or* use the pooler (pooler is usually simpler).
