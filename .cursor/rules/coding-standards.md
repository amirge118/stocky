# Coding Standards: Frontend & Backend

## General Principles

### Code Quality
- **Single Responsibility**: Keep functions small and focused on one task
- **DRY (Don't Repeat Yourself)**: Avoid code duplication, extract reusable functions
- **KISS (Keep It Simple, Stupid)**: Prefer simple solutions over complex ones
- **YAGNI (You Aren't Gonna Need It)**: Don't add functionality until needed
- **Clean Code**: Write code that is readable and self-documenting

### Naming Conventions
- **Descriptive Names**: Use clear, descriptive names that explain purpose
- **Consistent Style**: Follow language-specific naming conventions
- **Avoid Abbreviations**: Use full words unless abbreviation is widely understood
- **Boolean Names**: Use `is_`, `has_`, `can_` prefixes for booleans

## Frontend Standards (React/TypeScript)

### React Components
- **Functional Components**: Use functional components and hooks exclusively
- **Component Structure**: 
  1. Imports (external, then internal)
  2. Type definitions
  3. Component code
  4. Exports
- **Props**: Always define props with TypeScript interfaces
- **State**: Use descriptive state names (`isLoading`, not `loading`)

### TypeScript
- **No 'any'**: Never use `any` type, use `unknown` if type is truly unknown
- **Type Interfaces**: Always use TypeScript interfaces for API responses
- **Strict Mode**: Enable strict TypeScript mode
- **Type Inference**: Let TypeScript infer types when possible, but be explicit for public APIs

### Code Organization
- **File Structure**: Organize files by feature, not by type
- **Imports**: Group imports (external, then internal)
- **Exports**: Use named exports for components and utilities

## Backend Standards (Python/FastAPI)

### Python Style
- **PEP 8**: Follow PEP 8 style guide
- **Type Hints**: Use type hints for all function signatures
- **Docstrings**: Document all public functions and classes
- **Imports**: Organize imports (standard library, third-party, local)

### FastAPI Patterns
- **Pydantic Models**: Use Pydantic models for all request/response validation
- **Async Functions**: Use `async def` for all route handlers
- **Dependency Injection**: Use FastAPI's dependency injection system
- **Error Handling**: Use HTTPException for expected errors

### Code Organization
- **Layered Architecture**: Separate API, Service, and Data layers
- **File Naming**: Use lowercase with underscores (`stock_service.py`)
- **Function Names**: Use verbs for functions (`get_stock`, `create_user`)

## Common Standards

### Functions
- **Small Functions**: Keep functions under 50 lines when possible
- **Single Purpose**: Each function should do one thing well
- **Pure Functions**: Prefer pure functions (no side effects) when possible
- **Error Handling**: Handle errors explicitly, don't ignore them

### Comments
- **Why, Not What**: Explain why code exists, not what it does
- **Complex Logic**: Comment complex algorithms or business logic
- **TODOs**: Use TODO comments for future improvements
- **Avoid Obvious**: Don't comment obvious code

### Testing
- **Test Coverage**: Aim for 80%+ test coverage
- **Test Names**: Use descriptive test names that explain what is tested
- **Test Organization**: Organize tests by feature/component
- **Test Data**: Use fixtures for test data

## Key Rules

1. **Always** use TypeScript interfaces for API responses (no 'any')
2. **Always** use Pydantic models for request/response validation
3. **Always** keep functions small and modular (Single Responsibility Principle)
4. **Always** use functional components and hooks in React
5. **Always** use type hints in Python
6. **Always** handle errors explicitly
7. **Always** write tests for critical functionality
8. **Always** follow language-specific style guides
9. **Never** commit commented-out code
10. **Never** ignore linter warnings without good reason

For detailed frontend standards, see: [frontend/.cursorrules](../../frontend/.cursorrules)
For detailed backend standards, see: [backend/.cursorrules](../../backend/.cursorrules)
