# Tech Stack & Versions: Stock Insight App

## Overview
This document outlines the complete technology stack, specific versions, and best practices for each technology used in the Stock Insight App.

## Frontend Stack

### Core Framework
- **Next.js**: `15.1.0`
  - **Best Practice**: Use App Router exclusively (Pages Router deprecated)
  - **Key Features**: Server Components, Streaming, React Server Components
  - **Note**: React 19 compatibility, improved performance with Server Components
  - **Migration Note**: If upgrading from Next.js 14, ensure all routes use App Router

- **React**: `19.0.0`
  - **Best Practice**: Use functional components only, leverage Server Components
  - **Key Features**: Improved hydration, better error boundaries
  - **Note**: Breaking changes from React 18 - review migration guide
  - **Compatibility**: Fully compatible with Next.js 15

- **TypeScript**: `5.3.3`
  - **Best Practice**: Enable strict mode, use type-only imports
  - **Key Features**: Improved type inference, satisfies operator
  - **Note**: Use `satisfies` for better type checking without widening

### State Management
- **TanStack Query (React Query)**: `5.17.0`
  - **Best Practice**: Use for all server state, configure staleTime appropriately
  - **Key Features**: Automatic caching, background refetching, optimistic updates
  - **Note**: v5 has breaking changes from v4 - use QueryClientProvider
  - **Migration**: If upgrading from v4, update query keys and mutation syntax

### Forms & Validation
- **React Hook Form**: `7.49.3`
  - **Best Practice**: Use with Zod resolver for type-safe validation
  - **Key Features**: Minimal re-renders, uncontrolled components
  - **Note**: Works seamlessly with Zod schemas

- **Zod**: `3.22.4`
  - **Best Practice**: Match schemas with backend Pydantic models
  - **Key Features**: Type inference, runtime validation
  - **Note**: Keep schemas in sync with backend Pydantic schemas

### Styling
- **Tailwind CSS**: `3.4.1`
  - **Best Practice**: Use utility classes, configure theme in tailwind.config.ts
  - **Key Features**: JIT mode, arbitrary values, dark mode support
  - **Note**: Use `@apply` sparingly, prefer utility classes

- **Shadcn UI**: Latest (installed via CLI)
  - **Best Practice**: Copy components to your codebase, customize as needed
  - **Key Features**: Accessible, customizable, uses Radix UI primitives
  - **Note**: Components are copied, not installed as dependencies

### Testing
- **Jest**: `29.7.0`
  - **Best Practice**: Use with React Testing Library, test behavior not implementation
  - **Key Features**: Improved performance, better TypeScript support
  - **Note**: Configure with Next.js Jest preset

- **Playwright**: `1.41.0`
  - **Best Practice**: Use for E2E tests, test critical user flows
  - **Key Features**: Cross-browser testing, auto-waiting, fixtures
  - **Note**: Configure in playwright.config.ts

## Backend Stack

### Core Framework
- **FastAPI**: `0.109.0`
  - **Best Practice**: Use async/await, leverage dependency injection
  - **Key Features**: Automatic OpenAPI docs, async support, type hints
  - **Note**: Use lifespan context manager instead of @app.on_event
  - **Migration**: If upgrading from 0.100.x, check for breaking changes in middleware

- **Uvicorn**: `0.27.0`
  - **Best Practice**: Use with `[standard]` extras for better performance
  - **Key Features**: ASGI server, WebSocket support, auto-reload
  - **Note**: Use `--reload` for development, production workers for production

- **Python**: `3.11+`
  - **Best Practice**: Use type hints, async/await, dataclasses
  - **Key Features**: Improved performance, better error messages
  - **Note**: Python 3.12+ recommended for latest features

### Database
- **SQLAlchemy**: `2.0.25`
  - **Best Practice**: Use async sessions, select() instead of query()
  - **Key Features**: Async support, improved type hints, better performance
  - **Migration**: If upgrading from 1.4, use async API, update query syntax
  - **Note**: Use `selectinload`/`joinedload` for eager loading

- **asyncpg**: `0.29.0`
  - **Best Practice**: Use connection pooling, async operations
  - **Key Features**: Fast PostgreSQL driver, async support
  - **Note**: Faster than psycopg2 for async operations

- **Alembic**: `1.13.1`
  - **Best Practice**: Review auto-generated migrations, test before applying
  - **Key Features**: Database migrations, version control
  - **Note**: Always backup database before migrations

### Validation
- **Pydantic**: `2.5.3`
  - **Best Practice**: Use Field for validation, model_validator for complex validation
  - **Key Features**: v2 has better performance, improved validation
  - **Migration**: If upgrading from v1, update Config class to model_config
  - **Note**: Use `model_config` instead of `Config` class

### Authentication
- **python-jose**: `3.3.0`
  - **Best Practice**: Use HS256 for symmetric keys, RS256 for asymmetric
  - **Key Features**: JWT encoding/decoding, token validation
  - **Note**: Include `[cryptography]` extra for RS256 support

- **passlib**: `1.7.4`
  - **Best Practice**: Use bcrypt context, hash passwords before storing
  - **Key Features**: Multiple hashing algorithms, password verification
  - **Note**: Include `[bcrypt]` extra for bcrypt support

### External APIs
- **yfinance**: `0.2.33`
  - **Best Practice**: Cache responses, handle rate limits
  - **Key Features**: Yahoo Finance API wrapper, stock data retrieval
  - **Note**: May have rate limits, implement caching

- **httpx**: `0.26.0`
  - **Best Practice**: Use async client, configure timeouts
  - **Key Features**: Async HTTP client, better than requests for async
  - **Note**: Use for all external API calls

### AI/ML Services
- **OpenAI**: `1.10.0`
  - **Best Practice**: Use async client, handle rate limits, implement retries
  - **Key Features**: GPT models, embeddings, function calling
  - **Note**: v1.x has breaking changes from v0.x - update client initialization

- **Anthropic**: `0.18.1`
  - **Best Practice**: Use async client, handle rate limits
  - **Key Features**: Claude models, streaming support
  - **Note**: Keep API keys secure, use environment variables

### Development Tools
- **Black**: `24.1.1`
  - **Best Practice**: Use default line length (88), format on save
  - **Key Features**: Uncompromising code formatter
  - **Note**: Configure in pyproject.toml

- **Ruff**: `0.1.11`
  - **Best Practice**: Use as linter, faster than flake8
  - **Key Features**: Fast Python linter, replaces flake8/isort
  - **Note**: Configure rules in pyproject.toml

- **mypy**: `1.8.0`
  - **Best Practice**: Enable strict mode, check all files
  - **Key Features**: Static type checking
  - **Note**: Use type stubs for better checking

## Version Compatibility Matrix

### Frontend Compatibility
- Next.js 15.1.0 ↔ React 19.0.0 ✅
- React 19.0.0 ↔ TypeScript 5.3.3 ✅
- TanStack Query 5.17.0 ↔ React 19.0.0 ✅
- Zod 3.22.4 ↔ TypeScript 5.3.3 ✅

### Backend Compatibility
- FastAPI 0.109.0 ↔ Python 3.11+ ✅
- SQLAlchemy 2.0.25 ↔ asyncpg 0.29.0 ✅
- Pydantic 2.5.3 ↔ FastAPI 0.109.0 ✅
- Python 3.11+ ↔ asyncpg 0.29.0 ✅

## Version Upgrade Notes

### Frontend Upgrades
- **Next.js 14 → 15**: Requires React 19, review Server Components usage
- **React 18 → 19**: Breaking changes in error boundaries, review migration guide
- **TanStack Query 4 → 5**: Update query keys, mutation syntax changed

### Backend Upgrades
- **FastAPI 0.100 → 0.109**: Check middleware changes, lifespan context manager
- **Pydantic 1 → 2**: Update Config class to model_config, review validators
- **SQLAlchemy 1.4 → 2.0**: Use async API, update query syntax

## Security Considerations

### Frontend
- **Next.js**: Keep updated for security patches
- **React**: Monitor for security advisories
- **Dependencies**: Run `npm audit` regularly

### Backend
- **FastAPI**: Keep updated, use latest security patches
- **Python**: Use Python 3.11+ for security improvements
- **Dependencies**: Run `pip-audit` regularly
- **Secrets**: Never commit API keys, use environment variables

## Performance Considerations

### Frontend
- **Next.js 15**: Improved Server Components performance
- **React 19**: Better hydration performance
- **TanStack Query**: Automatic caching reduces API calls
- **Tailwind CSS**: JIT mode for faster builds

### Backend
- **FastAPI**: Async support for better concurrency
- **SQLAlchemy 2.0**: Improved query performance
- **asyncpg**: Faster than psycopg2 for async operations
- **Pydantic v2**: Faster validation than v1

## Best Practices Summary

### Version Management
1. **Pin Versions**: Pin exact versions in production
2. **Regular Updates**: Update dependencies regularly for security
3. **Test Upgrades**: Test thoroughly before upgrading major versions
4. **Changelog Review**: Review changelogs for breaking changes

### Compatibility
1. **Check Compatibility**: Verify version compatibility before upgrading
2. **Migration Guides**: Follow official migration guides
3. **Test Thoroughly**: Test all features after upgrades
4. **Rollback Plan**: Have rollback plan for production upgrades

### Security
1. **Security Patches**: Apply security patches immediately
2. **Audit Dependencies**: Regularly audit dependencies
3. **Update Regularly**: Keep dependencies updated
4. **Monitor Advisories**: Monitor security advisories

## Key Rules

1. **Always** pin exact versions in production
2. **Always** test upgrades in development first
3. **Always** review changelogs for breaking changes
4. **Always** keep security patches updated
5. **Always** verify version compatibility
6. **Never** upgrade multiple major versions at once
7. **Never** skip testing after upgrades
8. **Always** have rollback plan
9. **Always** document version changes
10. **Always** monitor for security advisories
