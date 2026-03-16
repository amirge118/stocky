# Project Structure Guide

This document explains the organization and structure of the Stock Insight App project.

## Root Directory Structure

```
stocky/
├── README.md                    # Main project README
├── FUTURE_IMPROVEMENTS.md      # All ideas and planned improvements
├── PROJECT_STRUCTURE.md         # This file - structure guide
├── scripts/                     # Utility scripts (see package.json for dev commands)
├── docs/                        # All documentation
│   ├── setup/                  # Setup and installation guides
│   ├── guides/                 # Development guides
│   ├── testing/                # Testing documentation
│   ├── features/               # Feature completion docs
│   └── design-docs/            # Design documents
├── frontend/                    # Next.js frontend application
├── backend/                     # FastAPI backend application
├── .cursor/                     # Cursor AI rules
│   └── rules/                   # Project rules and guidelines
└── scripts/                     # Utility scripts (use npm run setup, dev:all, etc.)
```

## Documentation Structure

### `docs/setup/` - Setup & Installation
- `QUICK_START.md` - Fastest way to get started
- `ENV_SETUP.md` - Environment variables configuration
- `RUN_SERVERS.md` - Server management guide
- `ARCHITECTURE_SETUP.md` - Project architecture overview
- `START_DEVELOPMENT.md` - Complete development setup

### `docs/testing/` - Testing Documentation
- `TESTING_WORKFLOW.md` - Testing guide and best practices
- `TESTING_SUMMARY.md` - Overview of test coverage
- `WHY_TESTS_MISSED.md` - Analysis and prevention measures

### `docs/features/` - Feature Documentation
- `STOCK_FEATURE_COMPLETE.md` - Stock feature implementation

### `docs/design-docs/` - Design Documents
- `001-stock-insight-app-overview.md` - App overview design doc

## Code Structure

### Frontend (`frontend/`)
```
frontend/
├── app/                         # Next.js 15 App Router
│   ├── (routes)/               # Route groups
│   ├── api/                    # API routes
│   └── page.tsx                 # Pages
├── components/                  # React components
│   ├── features/               # Feature-specific components
│   ├── shared/                 # Shared components
│   └── ui/                     # UI primitives
├── lib/                        # Utilities and API clients
│   ├── api/                    # API client functions
│   └── utils.ts                # Utility functions
├── types/                      # TypeScript type definitions
├── __tests__/                  # Unit and integration tests
└── e2e/                        # E2E tests
```

### Backend (`backend/`)
```
backend/
├── app/                        # Application code
│   ├── core/                   # Core configuration
│   ├── api/                     # API routes
│   │   └── v1/
│   │       ├── endpoints/      # Endpoint modules
│   │       └── router.py       # Main router
│   ├── models/                 # SQLAlchemy models
│   ├── schemas/                # Pydantic schemas
│   ├── services/               # Business logic
│   ├── repositories/           # Data access layer
│   ├── middleware/             # Custom middleware
│   └── utils/                  # Utility functions
├── tests/                      # Test suite
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── e2e/                    # E2E tests
└── alembic/                    # Database migrations
```

## File Naming Conventions

### Documentation Files
- **Setup guides**: `UPPERCASE_WITH_UNDERSCORES.md` (e.g., `QUICK_START.md`)
- **Feature docs**: `FEATURE_NAME_COMPLETE.md` (e.g., `STOCK_FEATURE_COMPLETE.md`)
- **Design docs**: `NNN-feature-name.md` (e.g., `001-stock-insight-app-overview.md`)

### Code Files
- **Python**: `snake_case.py` (e.g., `stock_service.py`)
- **TypeScript/React**: `PascalCase.tsx` for components, `camelCase.ts` for utilities
- **Test files**: `test_*.py` (backend) or `*.test.tsx` (frontend)

### Configuration Files
- **Config files**: `.filename` or `filename.config.js`
- **Environment files**: `.env`, `.env.example`, `.env.local`
- **Language-specific configs**: Place in respective directories
  - Python: `pyrightconfig.json`, `pyproject.toml` → `backend/`
  - TypeScript: `tsconfig.json` → `frontend/`
  - IDE: `.vscode/settings.json` → Root (workspace-level)

### Scripts
- **Setup scripts** → `scripts/` directory
- **Naming**: Use lowercase with hyphens (e.g., `setup-backend.sh`)
- **Documentation**: Document in `scripts/README.md`

## Rules & Guidelines

### `.cursor/rules/` - Project Rules
- `project-overview.md` - Global project rules
- `architecture.md` - Architecture guidelines
- `coding-standards.md` - Coding standards
- `testing-rules.md` - Testing guidelines
- `tech-stack-versions.md` - Tech stack documentation
- And more...

### `.cursorrules` Files
- `backend/.cursorrules` - Backend-specific rules
- `frontend/.cursorrules` - Frontend-specific rules

## Adding New Files

When adding new files:

1. **Check existing structure** - Look for similar files
2. **Follow directory conventions** - Place files in appropriate directories
3. **Use consistent naming** - Follow existing patterns
4. **Update documentation** - Add references in relevant docs
5. **Update FUTURE_IMPROVEMENTS.md** - If it's a new feature/idea

See `.cursor/rules/project-overview.md` for detailed file structure rules.

## Quick Reference

- **Main README**: `README.md`
- **Setup guides**: `docs/setup/`
- **Testing docs**: `docs/testing/`
- **Feature docs**: `docs/features/`
- **Future ideas**: `FUTURE_IMPROVEMENTS.md`
- **Project rules**: `.cursor/rules/`
