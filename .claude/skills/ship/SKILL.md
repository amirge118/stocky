---
name: ship
description: Ship code for Stocky — push to GitHub, merge to main, watch all CI checks, diagnose and fix any failures, and finish only when everything is green. Use when the user says /ship or "push and merge to main".
---

# Ship Skill — Push → CI → Fix → Done

Execute the following steps in order. Do not stop until Step 6 is reached.

---

## Step 1 — Pre-flight

```bash
git status
git log --oneline -3
```

- If there are **uncommitted changes**: stop and tell the user what files are dirty. Do not auto-commit.
- If the working tree is clean: continue.
- Note the current branch name.

---

## Step 2 — Push to GitHub

**If on `main`:**
```bash
git push origin main
```

**If on a feature branch:**
```bash
git push -u origin <branch>
gh pr create --title "<branch summary>" --body "Auto-shipped via /ship skill."
gh pr merge --merge --delete-branch
```
Wait for the PR merge to complete before proceeding.

---

## Step 3 — Get the CI run ID

```bash
gh run list --branch main --limit 1
```

Extract the run ID from the output (first column). Then watch it:

```bash
gh run view <run-id>
```

Poll every 30 seconds until `Status: completed`. Report the job list and which jobs are still in progress on each poll.

---

## Step 4 — Evaluate result

```bash
gh run view <run-id>
```

- **`Conclusion: success`** → go to Step 6 (done).
- **`Conclusion: failure`** → go to Step 5 (diagnose).
- **`Conclusion: cancelled` or `skipped`** → report to user and stop.

---

## Step 5 — Diagnose, fix, and re-push

### 5a — Fetch failure logs

```bash
gh run view <run-id> --log-failed
```

### 5b — Map the failing job to a fix strategy

| Failing job | Common cause | Fix approach |
|---|---|---|
| `ruff` | Unused import (F401), wrong import sort (I001), formatting | `cd backend && ruff check --fix . && ruff format .` |
| `mypy` | `Any` return type, missing annotation, `no-any-return` | Fix the type annotation in the flagged file |
| `pytest` | Test assertion failure, import error, missing fixture | Fix the failing test or the code it exercises |
| `playwright` / `e2e` | UI selector broke, API mock stale | Update the E2E test or fixture mock |
| `bandit` | Security-flagged pattern | Replace with safe equivalent |
| `build` / `tsc` | TypeScript type error | Fix the type in the flagged component/file |
| `coverage` | Coverage dropped below 80% | Add a unit test for the uncovered code |

### 5c — Read the source, apply the fix

1. Read the exact file and line number from the log.
2. Apply the minimal targeted fix — do not refactor surrounding code.
3. Commit:

```bash
git add <only the fixed files>
git commit -m "fix(ci): <one-line description of what was wrong>"
git push origin main
```

4. Return to **Step 3** with the new run ID from:

```bash
gh run list --branch main --limit 1
```

Repeat the loop until CI passes.

---

## Step 6 — Done

When `Conclusion: success`:

```bash
gh run view <run-id>
git log --oneline -1
```

Report to the user:
- "All CI checks passed ✓"
- List of jobs that ran (with their conclusions)
- The final commit SHA on main

The skill is complete.

---

## Rules

- **Never skip hooks** (`--no-verify`) or force-push without explicit user permission.
- **Never amend a commit** that has already been pushed — always create a new one.
- **Never commit unrelated files** — only stage the files changed by the fix.
- **Maximum 5 fix iterations** — if CI still fails after 5 loops, stop and explain the situation to the user rather than continuing blindly.
