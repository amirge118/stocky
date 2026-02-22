# Architecture Rules: Backend & Frontend Separation

## Core Architecture Principles

### 1. Separation of Concerns
- **Frontend**: Handles UI, user interactions, client-side state, and presentation logic
- **Backend**: Handles business logic, data processing, AI/ML operations, database operations, and API endpoints
- **Never mix**: Frontend should never contain business logic or direct database access
- **API Contract**: Frontend and Backend communicate exclusively through well-defined REST API endpoints

### 2. Project Structure

```
project-root/
├── frontend/                 # Next.js application
│   ├── app/                  # Next.js 15 App Router
│   │   ├── (routes)/         # Route groups
│   │   ├── api/              # API routes (if needed for server-side)
│   │   └── layout.tsx        # Root layout
│   ├── components/           # Reusable UI components
│   │   ├── ui/               # Shadcn UI components
│   │   └── features/         # Feature-specific components
│   ├── lib/                  # Utilities and helpers
│   │   ├── api/              # API client functions
│   │   └── utils/            # General utilities
│   ├── hooks/                # Custom React hooks
│   ├── types/                # TypeScript type definitions
│   └── public/               # Static assets
│
└── backend/                  # FastAPI application
    ├── app/
    │   ├── api/              # API route handlers
    │   │   └── v1/           # API versioning
    │   ├── core/             # Core configuration
    │   │   ├── config.py     # Settings and environment
    │   │   └── security.py   # Auth and security
    │   ├── models/           # Database models (SQLAlchemy)
    │   ├── schemas/          # Pydantic schemas (request/response)
    │   ├── services/         # Business logic layer
    │   ├── repositories/     # Data access layer (optional)
    │   └── main.py           # Application entry point
    ├── tests/                # Backend tests
    └── requirements.txt      # Python dependencies
```

## Frontend Architecture (Next.js)

### 3. Frontend Layer Responsibilities
- **Presentation Layer**: Render UI components, handle user interactions
- **State Management**: 
  - Use React hooks (useState, useReducer) for local component state
  - Use React Query/SWR for server state and API data caching
  - Use Context API sparingly for global UI state (theme, auth context)
- **API Communication**: 
  - Create dedicated API client functions in `lib/api/`
  - Use TypeScript interfaces for all API request/response types
  - Handle loading states, errors, and success states consistently
- **Routing**: Use Next.js App Router for all navigation
- **Server Components**: Prefer Server Components for data fetching when possible

### 4. Frontend API Client Pattern
```typescript
// lib/api/stock.ts
export interface StockResponse {
  symbol: string;
  price: number;
  // ... other fields
}

export async function getStockData(symbol: string): Promise<StockResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/stocks/${symbol}`);
  if (!response.ok) throw new Error('Failed to fetch stock data');
  return response.json();
}
```

### 5. Frontend Error Handling
- Use error boundaries for component-level error handling
- Display user-friendly error messages
- Log errors to monitoring service (e.g., Sentry)
- Never expose backend implementation details to users

## Backend Architecture (FastAPI)

### 6. Backend Layer Responsibilities
- **API Layer**: Define endpoints, handle HTTP requests/responses, validate input
- **Service Layer**: Implement business logic, orchestrate operations
- **Data Layer**: Database access, external API calls, data transformations
- **Security**: Authentication, authorization, input validation, rate limiting

### 7. Backend Layered Architecture
```
API Routes (FastAPI routers)
    ↓
Schemas (Pydantic validation)
    ↓
Services (Business logic)
    ↓
Repositories/Models (Data access)
    ↓
Database/External APIs
```

### 8. API Design Rules
- **RESTful Conventions**: Use standard HTTP methods (GET, POST, PUT, DELETE, PATCH)
- **URL Structure**: `/api/v1/resource/{id}/sub-resource`
- **Versioning**: Always version APIs (`/api/v1/`, `/api/v2/`)
- **Status Codes**: Use appropriate HTTP status codes (200, 201, 400, 401, 404, 500)
- **Response Format**: Consistent JSON structure with `data`, `error`, `message` fields
- **Documentation**: All endpoints must be documented via FastAPI's OpenAPI/Swagger

### 9. Request/Response Validation
- Use Pydantic models for all request bodies and query parameters
- Use Pydantic models for all response schemas
- Validate input at the API boundary (never trust client input)
- Return clear error messages with appropriate status codes

### 10. Error Handling Pattern
```python
# Consistent error response structure
{
    "error": {
        "code": "STOCK_NOT_FOUND",
        "message": "Stock symbol not found",
        "details": {}
    }
}
```

## Communication & Data Flow

### 11. API Communication Protocol
- **Format**: JSON for all request/response bodies
- **Headers**: 
  - `Content-Type: application/json`
  - `Authorization: Bearer <token>` for authenticated endpoints
- **CORS**: Configure CORS properly for frontend domain
- **Rate Limiting**: Implement rate limiting on backend API endpoints

### 12. Data Flow Pattern
```
User Action (Frontend)
    ↓
API Call (lib/api/*)
    ↓
HTTP Request (REST API)
    ↓
Backend Endpoint (FastAPI router)
    ↓
Validation (Pydantic schema)
    ↓
Service Layer (Business logic)
    ↓
Data Layer (Database/External API)
    ↓
Response (Pydantic schema)
    ↓
JSON Response
    ↓
Frontend Update (React state)
```

## Security Architecture

### 13. Authentication & Authorization
- **Frontend**: Store JWT tokens securely (httpOnly cookies preferred over localStorage)
- **Backend**: Validate JWT tokens on protected endpoints
- **API Keys**: Use environment variables for API keys (never commit to repo)
- **CORS**: Configure allowed origins explicitly

### 14. Input Validation
- **Frontend**: Client-side validation for UX (immediate feedback)
- **Backend**: Server-side validation is mandatory (never trust client)
- **Sanitization**: Sanitize all user inputs to prevent injection attacks

## State Management

### 15. Frontend State Strategy
- **Server State**: Use React Query or SWR for API data (caching, refetching, synchronization)
- **Client State**: Use React hooks (useState, useReducer) for UI state
- **Global State**: Use Context API only for truly global state (auth, theme)
- **Form State**: Use React Hook Form for form management

### 16. Backend State
- **Stateless**: Backend should be stateless (no session storage)
- **Database**: All persistent state stored in database
- **Cache**: Use Redis for caching frequently accessed data

## Testing Architecture

### 17. Frontend Testing
- **Unit Tests**: Test individual components and utilities
- **Integration Tests**: Test component interactions and API integration
- **E2E Tests**: Test critical user flows (Playwright/Cypress)

### 18. Backend Testing
- **Unit Tests**: Test service layer functions in isolation
- **API Tests**: Test endpoints with test client (FastAPI TestClient)
- **Integration Tests**: Test database operations and external API calls

## Deployment Architecture

### 19. Deployment Separation
- **Frontend**: Deploy as static site (Vercel, Netlify) or Node.js server
- **Backend**: Deploy as containerized service (Docker) on cloud platform
- **Environment Variables**: Separate `.env` files for frontend and backend
- **API Base URL**: Frontend must use environment variable for backend URL

### 20. Environment Configuration
```typescript
// Frontend: .env.local
NEXT_PUBLIC_API_BASE_URL=https://api.example.com
```

```python
# Backend: .env
DATABASE_URL=postgresql://...
OPENAI_API_KEY=...
CORS_ORIGINS=https://app.example.com
```

## Performance & Optimization

### 21. Frontend Optimization
- Use Next.js Image component for optimized images
- Implement code splitting and lazy loading
- Use React Query caching to minimize API calls
- Optimize bundle size (tree shaking, dynamic imports)

### 22. Backend Optimization
- Use async/await for all I/O operations
- Implement database query optimization (indexes, query optimization)
- Use caching (Redis) for expensive operations
- Implement pagination for list endpoints
- Use connection pooling for database connections

## Monitoring & Logging

### 23. Logging Strategy
- **Frontend**: Log errors to monitoring service (Sentry)
- **Backend**: Structured logging (JSON format) with log levels
- **API Logging**: Log all API requests/responses (with sensitive data redacted)

### 24. Monitoring
- **Frontend**: Monitor errors, performance metrics, user interactions
- **Backend**: Monitor API response times, error rates, database performance
- **Alerts**: Set up alerts for critical errors and performance degradation

## Key Rules Summary

1. **Never** put business logic in frontend
2. **Always** validate input on backend
3. **Always** use TypeScript interfaces for API contracts
4. **Always** version your APIs (`/api/v1/`)
5. **Always** document endpoints with OpenAPI
6. **Never** expose sensitive data in API responses
7. **Always** handle errors gracefully on both sides
8. **Always** use environment variables for configuration
9. **Keep** frontend and backend repositories separate or clearly separated
10. **Maintain** consistent API response structure
