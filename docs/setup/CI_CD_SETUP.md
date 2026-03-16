# CI/CD Pipeline Setup

This document describes the CI/CD pipeline for the three-branch strategy (`dev` / `test` / `main`) and how to configure branch protection and GitHub Environments.

## Branch Flow

- **Feature branches** → PR into `dev`
- **dev** → PR into `test` (promotion to staging)
- **test** → PR into `main` (promotion to production)
- No direct commits to `test` or `main`; all changes via PR. Tests must pass to merge (no approval required for solo developers).

**Note:** Ensure `dev` and `test` branches exist. Create them if needed: `git checkout -b dev && git push -u origin dev`

## Pipeline Overview

| Workflow | File | Trigger | Purpose |
|----------|------|---------|---------|
| **PR CI** | `pr-ci.yml` | PRs to `dev`, `test`, `main` | Fast lint, type-check, unit/component tests, coverage gates, build verification (test/main) |
| **Strict CI** | `strict-ci.yml` | Push to `test`, `main` | Full integration, E2E smoke, build and push images, security scan |
| **Staging Deploy** | `staging-deploy.yml` | After Strict CI on `test` | Deploy to staging environment |
| **Production Deploy** | `prod-deploy.yml` | After Strict CI on `main` | Deploy to production (automatic when tests pass) |

## Branch Protection Rules

Configure in **Repository** → **Settings** → **Branches** → **Add rule** (or edit existing).

### `dev` (development)

| Setting | Value |
|---------|-------|
| Branch name pattern | `dev` |
| Require a pull request before merging | Yes (0 approvals – tests are the gate) |
| Require status checks to pass | Yes |
| Require branches to be up to date | Yes |
| Required status checks | `Backend Tests`, `Frontend Tests` |
| Do not allow bypassing the above settings | Recommended |

### `test` (staging)

| Setting | Value |
|---------|-------|
| Branch name pattern | `test` |
| Require a pull request before merging | Yes (0 approvals – tests are the gate) |
| Require status checks to pass | Yes |
| Require branches to be up to date | Yes |
| Required status checks | `Backend Tests`, `Frontend Tests`, `Build Images` (add `E2E Smoke` when available) |
| Do not allow bypassing the above settings | Yes |

### `main` (production)

| Setting | Value |
|---------|-------|
| Branch name pattern | `main` |
| Require a pull request before merging | Yes (0 approvals – tests are the gate) |
| Require status checks to pass | Yes |
| Require branches to be up to date | Yes |
| Required status checks | `Backend Tests`, `Frontend Tests`, `Build Images` |
| Do not allow bypassing the above settings | Yes |

### Setup Steps

1. Go to **Settings** → **Branches**
2. Click **Add rule** for each branch (`dev`, `test`, `main`)
3. Enter the branch name pattern
4. Enable the options and add the required status checks as listed above
5. Save each rule

## GitHub Environments

Configure in **Settings** → **Environments**.

### `staging` (bound to `test`)

- No required reviewers
- Use for automatic deployment after merge to `test`
- Add environment-specific secrets (e.g. `STAGING_DATABASE_URL`, `STAGING_REDIS_URL`)

### `production` (bound to `main`)

- No required reviewers (solo developer – tests are the gate)
- Add environment-specific secrets (e.g. `PROD_DATABASE_URL`, `PROD_REDIS_URL`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`)

### Secrets Strategy

| Scope | Use for |
|-------|---------|
| Repository secrets | Shared CI tokens, build-time only |
| `staging` environment | Staging DB, Redis, API keys for staging |
| `production` environment | Production DB, Redis, API keys for production |

### Environment Setup Steps

1. Go to **Settings** → **Environments**
2. Click **New environment** → name it `staging`
3. Click **New environment** → name it `production`
4. For `production`: do **not** enable Required reviewers (tests are the gate for solo developers). If already set, remove them in Environment settings.
5. Add secrets to each environment:
   - `staging`: `STAGING_DATABASE_URL`, `STAGING_REDIS_URL`, `STAGING_SECRET_KEY`, etc.
   - `production`: `PROD_DATABASE_URL`, `PROD_REDIS_URL`, `PROD_SECRET_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.

## Release Tagging

On successful production deploy, a release tag is created: `vYYYYMMDD-<run_id>` (e.g. `v20240315-123`). Images are also tagged with `latest` and the run number for rollback reference.

## Post-Deploy Health Checks

Add `PROD_APP_URL` to the production environment secrets. The deploy workflow includes a placeholder for health checks. Extend the "Post-deploy health check" step to:

```bash
curl -f ${{ secrets.PROD_APP_URL }}/api/v1/health || exit 1
```

If the health check fails, trigger the rollback workflow manually.

## Rollback Strategy

Use the **Rollback** workflow (`rollback.yml`) when production has critical issues:

1. Go to **Actions** → **Rollback** → **Run workflow**
2. Enter the image tag to rollback to (e.g. previous run number `123`, or SHA `sha-abc123`)
3. Type `rollback` in the confirm field
4. Run the workflow

**Finding the rollback target:**
- Check **Packages** for image tags (run number, SHA)
- Check **Releases** for version tags
- Use the last known-good deployment tag

## Local Pre-commit Checks

Run before pushing:

```bash
# All tests
npm run test:all

# Backend only (with coverage)
cd backend && pytest tests -v --cov=app --cov-fail-under=80

# Frontend only (with coverage)
cd frontend && npm run test:coverage
```

## Coverage Thresholds (by branch)

| Branch | Backend | Frontend |
|--------|---------|----------|
| `dev` | 75% | 60% |
| `test` | 80% | 65% |
| `main` | 80% | 65% |

Config locations:
- Backend: `pytest --cov-fail-under=X` in workflow
- Frontend: `frontend/jest.config.js` → `coverageThreshold`
