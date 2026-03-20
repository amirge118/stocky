# AI agent rules — Stocky

Single sources of truth so **Cursor** and **Claude Code** stay aligned without duplicating long guides.

## Canonical by area

| Area | File |
|------|------|
| **Frontend** | [`frontend/.cursorrules`](../../frontend/.cursorrules) |
| **Backend** | [`backend/.cursorrules`](../../backend/.cursorrules) |
| **Project-wide** (structure, `FUTURE_IMPROVEMENTS.md`) | [`.cursor/rules/project-overview.md`](../../.cursor/rules/project-overview.md) |
| **Versions & stack matrix** | [`.cursor/rules/tech-stack-versions.md`](../../.cursor/rules/tech-stack-versions.md) |

## UI/UX Pro Max (optional design skill)

Installed under **`.cursor/skills/ui-ux-pro-max/`** (see [`ui-ux-pro-max.md`](./ui-ux-pro-max.md)). Use for inspiration and design-system search; **do not replace** [`frontend/.cursorrules`](../../frontend/.cursorrules) project conventions when they conflict.

## Superpowers (optional Cursor / Claude plugin)

[obra/superpowers](https://github.com/obra/superpowers) — workflow skills (brainstorming, plans, TDD, debugging, git worktrees, code review). **Install via IDE** (`/add-plugin superpowers` in Cursor), not files in this repo. See [`superpowers.md`](./superpowers.md). If a Superpowers workflow conflicts with Stocky’s Git/PR rules, prefer **`CONTRIBUTING.md`** and **`.cursor/rules/`**.

## Topic rules (`.cursor/rules/`)

Use when the task matches: **API** → `api-design-rules.md` · **DB** → `database-rules.md` · **Security** → `security-rules.md` · **Tests** → `testing-rules.md` · **Git/PR** → `git-workflow-rules.md`, `pr-review.md` · **Docker** → `docker-dev-workflow.md`.

Full index: [`.cursor/rules/README.md`](../../.cursor/rules/README.md).

## Claude Code

- **Skills:** `.claude/skills/*` should only point here (e.g. frontend skill → `frontend/.cursorrules`).
- **Permissions:** `.claude/settings.local.json` is separate (tool allowlists), not coding rules.

## Maintaining rules

When you change a convention, **edit the canonical file** above, not copies. Thin stubs (`frontend-nextjs-rules.md`, skills) should keep only pointers.
