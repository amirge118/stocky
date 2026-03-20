# Cursor rules — Stocky

Rules under `.cursor/rules/` supplement **canonical** per-app guides. Prefer editing those guides first, then topic files below.

## Canonical (single source)

| What | Where |
|------|--------|
| Frontend (including UI + React Query rules) | [`frontend/.cursorrules`](../../frontend/.cursorrules) |
| Backend | [`backend/.cursorrules`](../../backend/.cursorrules) |
| Project-wide + `FUTURE_IMPROVEMENTS.md` workflow | [`project-overview.md`](./project-overview.md) |
| Stack versions | [`tech-stack-versions.md`](./tech-stack-versions.md) |

**Cursor + Claude index:** [`docs/ai/README.md`](../../docs/ai/README.md)

## Topic files (use when relevant)

- **Architecture (short)** — [`architecture.md`](./architecture.md)
- **Coding style (short)** — [`coding-standards.md`](./coding-standards.md) · [`tech-preferences.md`](./tech-preferences.md)
- **API** — [`api-design-rules.md`](./api-design-rules.md)
- **Database** — [`database-rules.md`](./database-rules.md)
- **Errors** — [`error-handling-rules.md`](./error-handling-rules.md)
- **Security** — [`security-rules.md`](./security-rules.md)
- **Testing** — [`testing-rules.md`](./testing-rules.md)
- **Docs / design docs** — [`documentation-rules.md`](./documentation-rules.md) · [`design-docs-guide.md`](./design-docs-guide.md)
- **Workflow** — [`docker-dev-workflow.md`](./docker-dev-workflow.md) · [`git-workflow-rules.md`](./git-workflow-rules.md) · [`pr-review.md`](./pr-review.md)

## Thin stubs (pointers only)

- [`frontend-nextjs-rules.md`](./frontend-nextjs-rules.md) → `frontend/.cursorrules`
- [`python-fastapi-best-practices.md`](./python-fastapi-best-practices.md) → `backend/.cursorrules` + API/DB rules

## How to use

1. New feature: `architecture.md` or `docs/ai/README.md` for orientation, then `frontend/.cursorrules` or `backend/.cursorrules`.
2. API/DB/security/tests: open the matching topic file above.
3. Avoid copying the same paragraphs into multiple files — link instead.
