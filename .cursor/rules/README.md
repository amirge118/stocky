# Cursor Rules Documentation

This directory contains comprehensive rules and guidelines for the Stock Insight App project.

## Rules File Organization

### Core Architecture
- **[architecture.md](./architecture.md)** - High-level architecture overview for both frontend and backend
- **[project-overview.md](./project-overview.md)** - Project overview and communication protocol

### Technology Stack
- **[tech-stack-versions.md](./tech-stack-versions.md)** - Complete tech stack with versions, compatibility matrix, and best practices
- **[tech-preferences.md](./tech-preferences.md)** - Quick reference (references tech-stack-versions.md for details)

### Frontend Rules
- **[frontend/.cursorrules](../../frontend/.cursorrules)** - Comprehensive frontend architecture, project structure, and patterns
- **[frontend-nextjs-rules.md](./frontend-nextjs-rules.md)** - Detailed Next.js and React patterns (references frontend/.cursorrules)

### Backend Rules
- **[backend/.cursorrules](../../backend/.cursorrules)** - Comprehensive backend architecture, project structure, and patterns
- **[python-fastapi-best-practices.md](./python-fastapi-best-practices.md)** - Python/FastAPI best practices (references backend/.cursorrules)

### Standards & Guidelines
- **[coding-standards.md](./coding-standards.md)** - General coding standards for frontend and backend
- **[api-design-rules.md](./api-design-rules.md)** - REST API design conventions
- **[database-rules.md](./database-rules.md)** - Database design and query patterns
- **[error-handling-rules.md](./error-handling-rules.md)** - Error handling patterns
- **[security-rules.md](./security-rules.md)** - Security best practices
- **[testing-rules.md](./testing-rules.md)** - Testing strategies and patterns
- **[documentation-rules.md](./documentation-rules.md)** - Code documentation standards

### Workflow
- **[docker-dev-workflow.md](./docker-dev-workflow.md)** - Docker + npm scripts for dev; add new services to Docker
- **[git-workflow-rules.md](./git-workflow-rules.md)** - Git workflow and commit conventions
- **[pr-review.md](./pr-review.md)** - Pull request review guidelines

## File Relationships

### Primary Architecture Files
- `frontend/.cursorrules` - **Primary** frontend architecture reference
- `backend/.cursorrules` - **Primary** backend architecture reference
- `architecture.md` - High-level overview of both

### Supporting Files
- `frontend-nextjs-rules.md` - Detailed patterns (supplements frontend/.cursorrules)
- `python-fastapi-best-practices.md` - Quick reference (references backend/.cursorrules)
- `tech-stack-versions.md` - **Primary** tech stack reference
- `tech-preferences.md` - Quick reference (references tech-stack-versions.md)

## How to Use

1. **Starting a new feature**: Read `architecture.md` for overview, then refer to specific `frontend/.cursorrules` or `backend/.cursorrules`
2. **Choosing technologies**: See `tech-stack-versions.md` for versions and compatibility
3. **API design**: Follow `api-design-rules.md`
4. **Database work**: Follow `database-rules.md`
5. **Code review**: Use `pr-review.md` and `coding-standards.md`

## Notes on Duplication

Some files contain overlapping content by design:
- **Architecture files** (`frontend/.cursorrules`, `backend/.cursorrules`) contain comprehensive, detailed information
- **Pattern files** (`frontend-nextjs-rules.md`, `python-fastapi-best-practices.md`) provide quick reference and specific patterns
- **Overview files** (`architecture.md`, `tech-preferences.md`) provide high-level summaries

Files reference each other to avoid duplication while maintaining comprehensive coverage.
