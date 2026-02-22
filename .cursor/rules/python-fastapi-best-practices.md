# Python & FastAPI Best Practices

> **Note**: Comprehensive backend architecture and best practices are documented in `backend/.cursorrules`.
> 
> For detailed backend architecture, see: [backend/.cursorrules](../../backend/.cursorrules)
> 
> For FastAPI-specific patterns, see: [api-design-rules.md](./api-design-rules.md)
> 
> For database patterns, see: [database-rules.md](./database-rules.md)

## Core Principles

### Code Style
- **Functional Programming**: Prefer functions over classes when possible
- **Descriptive Names**: Use descriptive variable names with auxiliary verbs (e.g., `is_active`, `has_permission`)
- **File Naming**: Use lowercase with underscores (`stock_service.py`, not `StockService.py`)
- **Type Hints**: Always use type hints for all function signatures
- **Pydantic Models**: Prefer Pydantic models over raw dictionaries for validation

### FastAPI Patterns
- **Async First**: Use `async def` for all route handlers and I/O operations
- **Dependency Injection**: Use FastAPI's dependency injection system
- **Lifespan Context**: Use lifespan context manager instead of `@app.on_event`
- **Pydantic v2**: Use `model_config` instead of `Config` class
- **Error Handling**: Use `HTTPException` for expected errors, global handlers for unexpected

### Database Patterns
- **SQLAlchemy 2.0**: Use `select()` instead of `query()`, use async sessions
- **Async Operations**: Use `asyncpg` for PostgreSQL async operations
- **Eager Loading**: Use `selectinload`/`joinedload` for relationship loading
- **Migrations**: Use Alembic for database migrations

### Performance
- **Async I/O**: Use async operations for all database calls and external API requests
- **Caching**: Implement caching for frequently accessed data (Redis)
- **Connection Pooling**: Use connection pooling for database connections
- **Lazy Loading**: Use lazy loading for large datasets

## Key Rules Summary

1. **Always** use `async def` for route handlers
2. **Always** use type hints
3. **Always** validate input with Pydantic
4. **Always** use async database operations
5. **Never** use blocking I/O
6. **Always** handle errors properly
7. **Always** use dependency injection
8. **Always** document endpoints
9. **Always** write tests
10. **Always** follow PEP 8 style guide

For comprehensive details, refer to `backend/.cursorrules`.
