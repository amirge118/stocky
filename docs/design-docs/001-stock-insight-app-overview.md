# Stock Insight App - System Design Overview

## Status
Approved

## Overview
Stock Insight App is a financial stock analysis platform that provides daily, weekly, and monthly insights using AI. The system consists of a Next.js frontend and FastAPI backend communicating via REST API.

## Problem Statement
Investors and traders need:
- Real-time stock data and analysis
- AI-powered insights and recommendations
- Historical data visualization
- Easy-to-use interface for stock research

## Goals
- Provide real-time stock data from Yahoo Finance
- Generate AI-powered insights using OpenAI/Anthropic
- Display data in an intuitive, responsive UI
- Support daily, weekly, and monthly analysis
- Fast API response times (< 200ms for most endpoints)
- Scalable architecture for future growth

## Non-Goals
- Real-time trading execution (read-only analysis)
- Portfolio management features (v1)
- Social features or user sharing (v1)
- Mobile app (web-first approach)

## Architecture

### High-Level Architecture
```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Browser   │────────▶│  Next.js    │────────▶│  FastAPI    │
│  (Frontend) │         │  Frontend   │         │  Backend    │
└─────────────┘         └─────────────┘         └─────────────┘
                                                       │
                                                       ├──▶ PostgreSQL
                                                       ├──▶ yfinance API
                                                       ├──▶ OpenAI API
                                                       └──▶ Anthropic API
```

### Component Breakdown

#### Frontend (Next.js 15)
- **App Router**: File-based routing with Server Components
- **State Management**: TanStack Query for server state
- **UI Components**: Shadcn UI + Tailwind CSS
- **API Client**: Centralized API functions in `lib/api/`

#### Backend (FastAPI)
- **API Layer**: REST endpoints with OpenAPI documentation
- **Service Layer**: Business logic and orchestration
- **Data Layer**: SQLAlchemy models and database operations
- **External APIs**: yfinance, OpenAI, Anthropic clients

### Data Flow

```
User Request
    ↓
Frontend API Client (lib/api/)
    ↓
HTTP Request (REST API)
    ↓
FastAPI Router
    ↓
Pydantic Validation
    ↓
Service Layer (Business Logic)
    ↓
Repository/Model Layer (Data Access)
    ↓
Database/External API
    ↓
Response (Pydantic Schema)
    ↓
JSON Response
    ↓
Frontend Update (React Query)
```

## Key Design Decisions

### 1. Separation of Frontend and Backend
**Decision**: Separate Next.js frontend and FastAPI backend
**Rationale**: 
- Independent scaling
- Technology flexibility
- Clear separation of concerns
- Team can work independently

### 2. REST API Communication
**Decision**: Use REST API instead of GraphQL
**Rationale**:
- Simpler for this use case
- Better tooling (FastAPI auto-docs)
- Easier to cache
- Team familiarity

### 3. PostgreSQL Database
**Decision**: Use PostgreSQL with SQLAlchemy
**Rationale**:
- Reliable and proven
- Good for relational data (stocks, users, insights)
- Strong async support (asyncpg)
- Free and open-source

### 4. Server Components First
**Decision**: Default to Next.js Server Components
**Rationale**:
- Better performance (less JavaScript)
- Direct data fetching
- SEO benefits
- Reduced client-side complexity

### 5. TanStack Query for Client State
**Decision**: Use TanStack Query for server state
**Rationale**:
- Automatic caching
- Background refetching
- Optimistic updates
- Better UX

## Security Considerations

- **Authentication**: JWT tokens with httpOnly cookies
- **API Keys**: Stored in environment variables, never committed
- **Input Validation**: Pydantic validation on all inputs
- **CORS**: Configured for specific origins only
- **Rate Limiting**: Implemented on API endpoints

## Performance Considerations

- **Database Indexing**: Indexes on frequently queried columns
- **Caching**: Redis for expensive operations (optional)
- **API Caching**: React Query caching on frontend
- **Image Optimization**: Next.js Image component
- **Code Splitting**: Dynamic imports for large components

## Scalability Considerations

- **Stateless Backend**: Can scale horizontally
- **Database Connection Pooling**: Handles concurrent requests
- **CDN**: Frontend can be served via CDN
- **Caching Strategy**: Reduces database load

## Testing Strategy

- **Unit Tests**: Test services and utilities in isolation
- **Integration Tests**: Test API endpoints
- **E2E Tests**: Test critical user flows
- **Target Coverage**: 80%+ for critical paths

## Migration Plan

### Phase 1: Core Infrastructure ✅
- [x] Project structure
- [x] Environment setup
- [x] Basic API structure

### Phase 2: Stock Data (In Progress)
- [ ] Stock data models
- [ ] yfinance integration
- [ ] Stock search endpoint

### Phase 3: AI Insights
- [ ] OpenAI/Anthropic integration
- [ ] Insight generation service
- [ ] Insight storage

### Phase 4: Frontend
- [ ] Stock search UI
- [ ] Stock detail page
- [ ] Insights display

## Open Questions

- [ ] Should we cache stock data? (How long?)
- [ ] What's the rate limit for yfinance API?
- [ ] Should insights be pre-generated or on-demand?
- [ ] Do we need user authentication in v1?

## Timeline

- **Week 1-2**: Core infrastructure and stock data
- **Week 3-4**: AI insights integration
- **Week 5-6**: Frontend implementation
- **Week 7**: Testing and optimization

## References

- [Architecture Rules](../.cursor/rules/architecture.md)
- [Tech Stack Versions](../.cursor/rules/tech-stack-versions.md)
- [API Design Rules](../.cursor/rules/api-design-rules.md)
