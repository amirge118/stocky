# Future Improvements

This document tracks all ideas, features, and improvements for the Stock Insight App. Every request, feature idea, or improvement suggestion should be added here for future consideration.

## Testing Improvements

### From Testing Summary

- [x] **CI/CD Pipeline** [HIGH] ✓
  - Set up CI/CD pipeline to enforce test coverage
  - Block merges if tests fail or coverage is below threshold
  - Automated deployment on successful test runs

- [ ] **Automated Test Generation** [LOW]
  - Generate test templates for common patterns
  - Create test scaffolding tools
  - Auto-generate tests for CRUD operations
  - Generate mock data factories

### רעיונות חדשים

- [x] **E2E Tests with Playwright** [MEDIUM] ✓
  - Add end-to-end tests for critical user flows (login, add stock, portfolio)
  - Run E2E in CI on every PR
  - Visual regression testing for key pages

- [ ] **Snapshot Testing for UI** [LOW]
  - Add Jest snapshot tests for shared components
  - Catch unintended UI changes in PRs

- [ ] **Mutation Testing** [LOW]
  - Use mutmut or similar to verify test quality
  - Identify tests that don't actually assert behavior

## Backend Improvements

### Database & Performance

- [ ] Add database connection pooling optimization
- [ ] Add database query optimization and indexing strategy review
- [ ] Implement database read replicas for scaling
- [ ] Add database migration rollback strategies
- [ ] Implement database backup and recovery procedures

### API Enhancements

- [ ] Add API rate limiting per user/IP
- [ ] Implement API versioning strategy (v2, v3)
- [ ] Add GraphQL endpoint as alternative to REST
- [ ] Implement API analytics and usage tracking
- [ ] Add API documentation improvements (more examples)
- [ ] Implement API deprecation warnings

### Authentication & Security

- [ ] Implement OAuth2 authentication (Google, GitHub)
- [ ] Add two-factor authentication (2FA)
- [ ] Implement role-based access control (RBAC)
- [ ] Add API key management for third-party integrations
- [ ] Implement session management and refresh tokens
- [ ] Add security audit logging
- [ ] Implement rate limiting per authenticated user
- [ ] Add IP whitelisting for admin endpoints

### Features

- [x] **Portfolio Day P&L + Today's Movers** [DONE]
  - Day change ($ and %) in portfolio summary
  - Today's leaders/losers strip with links to stock detail
- [x] **Portfolio News Feed** [DONE]
  - Unified news for all holdings at /portfolio
  - Breaking badge for news < 3h old
- [x] **Sector Overview Upgrade** [DONE]
  - Sector peers with price, day %, P/E, market cap
  - Compare All button to /stocks/compare
- [x] **Portfolio Performance Chart** [DONE]
  - Historical portfolio value (1M, 6M, 1Y) computed from holdings
- [x] **Compare Fundamentals + AI Summary** [DONE]
  - Metrics table (P/E, market cap, dividend, beta, 52W range)
  - AI comparison summary for 2–5 stocks
- [x] **Sector News Tab** [DONE]
  - Sector-level news via sector ETF (XLK, XLV, etc.) on stock detail
- [x] **Sector Trend Card** [DONE]
  - Sector performance % (day change) on portfolio page
- [x] **Portfolio & Stock Tests** [DONE]
  - Unit: holding_service (day P&L, news, history), stock_service (sector filter)
  - Integration: portfolio endpoints (GET, news, history, add)
  - Frontend: PortfolioSummaryCard, PortfolioNewsFeed (requires @testing-library/dom)
- [ ] Add historical stock data analysis (multi-year charts, dividends)
- [ ] Add social features (share insights, comments)
- [ ] Add technical indicators calculation (RSI, MACD, moving averages)
- [ ] Implement backtesting capabilities

### רעיונות חדשים

### Monitoring & Observability

- [ ] Add application performance monitoring (APM)
- [ ] Implement structured logging with correlation IDs
- [ ] Add error tracking and alerting (Sentry)
- [ ] Implement health check improvements (database, Redis, external APIs)
- [ ] Add metrics collection (Prometheus)
- [ ] Implement distributed tracing
- [ ] Add log aggregation and analysis

## Frontend Improvements

### Dependencies & Compatibility

- [ ] **Update Radix UI packages for React 19 compatibility** [MEDIUM]
  - Current: React 19 ref deprecation warnings from `@radix-ui/react-slot` and other Radix UI components
  - Issue: "Accessing element.ref was removed in React 19" console warnings
  - Solution: Update all `@radix-ui/*` packages to latest versions that support React 19
  - Status: Waiting for Radix UI to release React 19-compatible versions
  - Note: Warning is harmless and doesn't affect functionality

### User Experience

- [ ] Add dark/light mode toggle (user preference persisted)
- [ ] Implement responsive design improvements
- [ ] Add keyboard navigation support
- [ ] Implement accessibility improvements (WCAG 2.1 AA)
- [ ] Add loading skeletons instead of spinners
- [ ] Implement optimistic UI updates
- [ ] Add offline support with service workers
- [ ] Implement progressive web app (PWA) features

### Performance

- [ ] Implement code splitting and lazy loading
- [ ] Add image optimization and lazy loading
- [ ] Implement virtual scrolling for large lists
- [ ] Add request deduplication
- [ ] Implement request caching strategies
- [ ] Add bundle size optimization
- [ ] Implement server-side rendering (SSR) improvements

### Features

- [ ] Add stock search with autocomplete (dropdown suggestions while typing)
- [ ] Implement advanced filtering and sorting
- [ ] Add export functionality (CSV, PDF)
- [ ] Implement data visualization improvements

### רעיונות חדשים

- [x] **Shareable Stock URLs** [MEDIUM] ✓
  - Encode selected symbols in URL (e.g. /stocks?symbols=AAPL,MSFT)
  - Allow sharing comparison or watchlist views

- [ ] **Infinite Scroll for Stock List** [LOW]
  - Replace pagination with infinite scroll for smoother browsing
  - Virtualize list for performance

- [ ] **Drag-and-Drop Portfolio Reordering** [LOW]
  - Let users reorder holdings by drag-and-drop
  - Persist order preference

- [ ] **Agent Report Favorites** [LOW]
  - Pin favorite agent reports to dashboard
  - Quick access to frequently referenced analyses

### State Management

- [ ] Consider Zustand for global state management
- [ ] Implement optimistic updates for mutations
- [ ] Add offline state synchronization
- [ ] Implement state persistence (localStorage)
- [ ] Add state debugging tools

## Infrastructure & DevOps

### Deployment

- [ ] Add Kubernetes deployment configurations
- [ ] Implement blue-green deployment strategy
- [ ] Add canary releases
- [ ] Implement automated rollback procedures

### רעיונות חדשים

- [x] **GitHub Actions CI** [HIGH] ✓
  - Run tests, lint, type-check on every push/PR
  - Build Docker images on main branch
  - Optional: deploy to staging on merge

- [x] **Staging Environment** [MEDIUM] ✓
  - Dedicated staging URL for pre-production testing
  - Seed data for demo/testing

- [x] **Database Backup Automation** [MEDIUM] ✓
  - Scheduled pg_dump to object storage (S3, etc.)
  - Point-in-time recovery capability

### Environment Management

- [ ] Add environment-specific configurations
- [ ] Implement feature flags system
- [ ] Add secrets management (Vault, AWS Secrets Manager)
- [ ] Implement configuration management improvements

### Monitoring & Logging

- [ ] Set up centralized logging (ELK stack, CloudWatch)
- [ ] Implement log retention policies
- [ ] Add alerting for critical errors
- [ ] Implement uptime monitoring
- [ ] Add performance monitoring dashboards

## Documentation

- [ ] Add API documentation improvements (OpenAPI/Swagger)
- [ ] Create developer onboarding guide
- [ ] Add architecture decision records (ADRs)
- [ ] Implement inline code documentation improvements
- [ ] Add user documentation and guides
- [ ] Create troubleshooting guides
- [ ] Add deployment runbooks

### רעיונות חדשים

- [x] **CONTRIBUTING.md** [MEDIUM] ✓
  - How to set up dev environment, run tests, submit PRs
  - Code style and commit message conventions

- [ ] **API Changelog** [LOW]
  - Document breaking changes and new endpoints per version
  - Keep in sync with API versioning

## Code Quality

- [ ] Implement stricter TypeScript configurations (frontend)
- [ ] Add code review guidelines
- [ ] Implement automated code quality checks
- [ ] Add dependency vulnerability scanning
- [ ] Implement license compliance checking

### רעיונות חדשים

- [x] **Dependabot / Renovate** [MEDIUM] ✓
  - Automated PRs for dependency updates
  - Keep security patches applied quickly

- [ ] **SonarQube or CodeClimate** [LOW]
  - Code quality and security analysis
  - Technical debt visibility

## Security

- [ ] Add security headers (CSP, HSTS, etc.)
- [ ] Implement input sanitization improvements
- [ ] Add SQL injection prevention review
- [ ] Implement XSS prevention improvements
- [ ] Add CSRF protection
- [ ] Implement security audit automation

### רעיונות חדשים

- [x] **Rate Limiting on Auth Endpoints** [HIGH] ✓
  - Throttle login/register to prevent brute force
  - Per-IP and per-user limits

- [ ] **CORS Validation** [LOW]
  - Strict allowlist of origins in production
  - Reject unexpected preflight requests

## How to Add Ideas

When suggesting or implementing features:

1. **Add to this file** - Every idea should be documented here
2. **Categorize** - Place ideas in appropriate sections
3. **Prioritize** - Mark high-priority items with [HIGH]
4. **Link to issues** - Reference GitHub issues or tickets if applicable
5. **Add context** - Include why this improvement is valuable

## Priority Legend

- `[HIGH]` - High priority, should be implemented soon
- `[MEDIUM]` - Medium priority, nice to have
- `[LOW]` - Low priority, future consideration
- `[BLOCKED]` - Blocked by other dependencies

---

**Last Updated**: 2026-03-14
**Total Ideas**: ~90
