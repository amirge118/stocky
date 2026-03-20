# Architecture — Stocky

High-level split only. **Details live in the canonical stack files** (avoid duplicating long sections here).

## Principles

- **Frontend:** UI, client state, presentation. No business logic or direct DB access.
- **Backend:** APIs, validation, services, persistence, external data, AI tasks.
- **Contract:** JSON REST under `/api/v1/…`. OpenAPI/Swagger on the FastAPI app.

## Layout

```
frontend/     Next.js 15 App Router, TanStack Query, Tailwind, features under components/features/
backend/      FastAPI, SQLAlchemy 2 async, Pydantic v2, services + api/v1/endpoints/
```

## Layers (backend)

```
HTTP router → Pydantic schemas → Services → Models / DB / external APIs
```

## Read next

| Topic | Where |
|--------|--------|
| Frontend patterns, API client, React Query, UI tokens | [`frontend/.cursorrules`](../../frontend/.cursorrules) |
| Backend patterns, DB checks, structure | [`backend/.cursorrules`](../../backend/.cursorrules) |
| Versions | [`tech-stack-versions.md`](./tech-stack-versions.md) |
| REST shape, errors | [`api-design-rules.md`](./api-design-rules.md) |
| Agents & index | [`docs/ai/README.md`](../../docs/ai/README.md) |
