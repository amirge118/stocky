# Future Improvements

Ideas, features, and improvements for the Stocky Stock Insight App.
Every request, feature idea, or improvement suggestion should be added here.

---

## Performance

### Frontend

- [ ] **ESLint 10 upgrade** [LOW] — Blocked: `eslint-plugin-react` + flat config hit `context.getFilename` errors under ESLint 10; retry when `eslint-config-next` / plugins declare support
- [ ] **Tighten React Compiler ESLint rules** [LOW] — Re-enable `react-hooks/set-state-in-effect` / `immutability` after refactors (currently off for pragmatic CI)
- [ ] **Code splitting and lazy loading** [HIGH] — Route-level `next/dynamic` for heavy pages (Compare, Indicators)
- [ ] **Virtual scrolling for large lists** [MEDIUM] — Virtualize portfolio/watchlist rows (react-virtual) when count > 100
- [ ] **Bundle size optimization** [MEDIUM] — Analyze with `@next/bundle-analyzer`; tree-shake unused Recharts/Radix primitives
- [ ] **Request deduplication** [MEDIUM] — Deduplicate concurrent TanStack Query fetches for the same symbol
- [ ] **Request caching strategies** [MEDIUM] — Set appropriate `staleTime` / `gcTime` per query type (prices: 30s, fundamentals: 5m, news: 2m)
- [ ] **Image optimization and lazy loading** [LOW] — Use `next/image` for all logo/chart images
- [ ] **SSR improvements** [LOW] — Pre-render market overview and landing page data at build time via `generateStaticParams`
- [ ] **Optimistic UI updates** [MEDIUM] — Instant feedback on add/remove holding and watchlist mutations before server confirms
- [ ] **Portfolio performance over time chart** [LOW] — Restore removed `PortfolioPerformanceChart` (Recharts + `/api/v1/portfolio/history`) on portfolio page if users want historical value curve again

### Backend

- [ ] **Database connection pooling optimization** [HIGH] — Tune SQLAlchemy async pool size; add pool pre-ping; expose pool stats
- [ ] **Database query optimization and indexing** [HIGH] — Add composite indexes on `(user_id, symbol)` for holdings and watchlists; profile slow queries with `EXPLAIN ANALYZE`
- [ ] **Redis response caching for yfinance** [HIGH] — Cache `GET /api/v1/stocks/{symbol}` and market overview responses in Redis with TTL 60s; avoid repeated yfinance fetches on bursty loads
- [ ] **Database read replicas** [LOW] — Route read-heavy queries (holdings list, news) to read replica
- [ ] **Database migration rollback strategies** [LOW] — Document and test `alembic downgrade` paths for every migration

---

## UX / UI

### Interactions & Animations

- [ ] **Animate gain/loss color transitions on price updates** [HIGH] — Flash green→neutral / red→neutral on live price changes; use CSS transition on `color` + brief `background-color` highlight
- [ ] **MACD histogram per-bar coloring** [MEDIUM] — Color bars individually (green above 0, red below 0) using Recharts `<Cell>`
- [ ] **Skeleton shimmer consistency** [MEDIUM] — Replace bare `animate-pulse` with `skeleton-shimmer` CSS class across all loading states (portfolio, watchlist, stock detail, sector)
- [ ] **Gradient border hover variant for cards** [LOW] — Glow-blue border on hover for interactive cards (stock rows, comparison card)

### Navigation & Accessibility

- [ ] **Keyboard Shortcuts** [HIGH] — `⌘K` global search, `P` / `W` / `M` for Portfolio / Watchlist / Market navigation; shortcut hints in Navbar tooltip
- [ ] **Keyboard navigation support** [MEDIUM] — Full tab-key flow through tables, modals, and forms; visible focus ring in zinc-400
- [ ] **Accessibility improvements (WCAG 2.1 AA)** [MEDIUM] — Audit with axe-core; fix missing `aria-label` on icon buttons; ensure 4.5:1 contrast on zinc-400 text
- [ ] **Responsive design improvements** [MEDIUM] — Portfolio table horizontal scroll on mobile; sidebar collapses to bottom nav on small screens
- [ ] **Dark/light mode toggle** [LOW] — User preference persisted to localStorage; CSS variable swap; respect `prefers-color-scheme` default

### Polish

- [ ] **Replace `text-[10px]` in landing hero** [LOW] — Use `text-xs` as part of a landing page polish pass
- [ ] **Standardize SectorBreakdownTable + StockSectorOverview column headers** [LOW] — Use `.section-label` utility class uniformly
- [ ] **`.card-surface` utility class sweep** [LOW] — Ensure all feature panels use `rounded-xl border border-zinc-800 bg-zinc-900` via a shared utility

---

## Deployment & Infrastructure

### Deployment Strategy

- [ ] **Kubernetes deployment configurations** [MEDIUM] — Helm chart for backend + frontend + Celery worker; HPA based on CPU
- [ ] **Blue-green deployment strategy** [MEDIUM] — Zero-downtime deploys via two identical production slots
- [ ] **Canary releases** [LOW] — Route 5% of traffic to new version; auto-rollback on error rate spike
- [ ] **Automated rollback procedures** [LOW] — GitHub Actions `workflow_dispatch` to redeploy previous Docker image

### Environment & Secrets

- [ ] **Feature flags system** [MEDIUM] — Simple DB-backed or env-var feature flags to gate unreleased features per environment
- [ ] **Secrets management** [MEDIUM] — Move API keys to AWS Secrets Manager / Vault; never hardcode in `.env`
- [ ] **Environment-specific configurations** [LOW] — Separate `settings_dev / settings_staging / settings_prod` Pydantic config classes

### Monitoring & Observability

- [ ] **Error tracking with Sentry** [HIGH] — Integrate `sentry-sdk` in FastAPI + Sentry browser SDK in Next.js; capture unhandled exceptions with stack traces
- [ ] **Application performance monitoring (APM)** [MEDIUM] — Track p50/p95/p99 latency per endpoint; alert on regression
- [ ] **Metrics collection with Prometheus** [MEDIUM] — Expose `/metrics` via `prometheus-fastapi-instrumentator`; Grafana dashboard for request rate, error rate, DB pool usage
- [ ] **Structured logging with correlation IDs** [MEDIUM] — Inject `X-Request-ID` header; include in all log lines; propagate to Celery tasks
- [ ] **Health check improvements** [MEDIUM] — Add `/health/detailed` that checks DB, Redis, and yfinance reachability
- [ ] **Uptime monitoring** [LOW] — Ping `/health` every 60s from an external monitor (Better Uptime, UptimeRobot)
- [ ] **Centralized logging** [LOW] — Ship structured logs to ELK stack or CloudWatch Logs
- [ ] **Distributed tracing** [LOW] — OpenTelemetry spans across FastAPI → Celery → yfinance calls

---

## New Features

### HIGH Priority

- [ ] **Earnings Calendar** [HIGH]
  - Dedicated `/earnings` page + upcoming-earnings widget on portfolio page
  - Show date, EPS estimate, previous EPS, expected move % for all portfolio + watchlist symbols
  - Backend: `yfinance` `Ticker.calendar` + `earnings_dates` → new `earnings_service.py`
  - New endpoint: `GET /api/v1/stocks/{symbol}/earnings`
  - Frontend: timeline/table view, color-coded by days until earnings

- [ ] **AI Portfolio Health Coach** [HIGH]
  - Claude AI analyzes entire portfolio: concentration risk, sector imbalance, correlation, overweight positions
  - Actionable plain-language recommendations ("Your portfolio is 60% tech — consider diversifying")
  - Backend: `POST /api/v1/portfolio/ai-analysis` using `anthropic` SDK (same pattern as existing agent report)
  - Frontend: "AI Coach" card/tab on portfolio page with streaming output

- [ ] **Backend-Driven Alert Checker Cron Job** [HIGH]
  - Fire Telegram/WhatsApp alerts even when browser is closed
  - Celery Beat scheduled task polls active alerts vs live yfinance prices every 60s
  - Already has infrastructure: `backend/app/celery_app.py`, `backend/app/tasks/alert_tasks.py`

### MEDIUM Priority

- [ ] **Price Target Consensus Panel** [MEDIUM]
  - On stock detail: analyst buy / hold / sell count + average price target vs current price
  - Upside/downside % with color-coded progress bar
  - `yfinance`: `Ticker.analyst_price_targets`, `recommendations_summary`
  - New "Analyst Consensus" tab in StockDetail

- [ ] **Portfolio Rebalancing Wizard** [MEDIUM]
  - Set target allocation % per symbol; app shows current vs target drift
  - "Generate Rebalance Plan" produces a buy/sell trade list to return to targets
  - Backend: `GET /api/v1/portfolio/rebalancing-plan?targets=AAPL:0.20,NVDA:0.15,...`
  - Frontend: allocation sliders + trade preview table in a modal

- [ ] **Options Chain Viewer** [MEDIUM]
  - Calls and puts for any symbol with expiration date selector
  - Columns: Strike, Last, Bid, Ask, IV, Open Interest, Volume, Delta; highlight ITM rows
  - `yfinance`: `Ticker.option_chain(date)`
  - New endpoint: `GET /api/v1/stocks/{symbol}/options?expiry=YYYY-MM-DD`

- [ ] **Economic Calendar** [MEDIUM]
  - Macro events timeline: FOMC, CPI, PCE, NFP, GDP; expected vs actual (color-coded surprise)
  - Backend: integrate free public macro calendar API or curated static schedule
  - Frontend: `/market/calendar` page + widget on market overview

- [ ] **Stock Screener with Multi-Filter UI** [MEDIUM]
  - Filter by sector, P/E range, market cap, dividend yield, analyst rating, 52W performance
  - Save / share screener configurations via URL params

### LOW Priority

- [ ] **News Sentiment Score** [LOW]
  - AI-powered "Bullish / Neutral / Bearish" badge per stock based on recent headlines
  - Uses existing news feed + Claude API; cached per symbol per hour

- [ ] **Stock Heatmap by Sector** [LOW]
  - Treemap of S&P 500 colored by day % change, sized by market cap
  - Click cell to open stock detail

- [ ] **Portfolio Transaction History + Tax Lots** [LOW]
  - Track individual buy/sell events, not just current holdings
  - FIFO/LIFO cost basis; realized vs unrealized capital gains report

- [ ] **Custom Watchlist Groups** [LOW]
  - Multiple named watchlists ("Tech Picks", "Dividend Stocks")
  - Drag-drop symbols between groups

- [ ] **Dividend Income Projection** [LOW]
  - Per-holding and total annual dividend income on portfolio page
  - Monthly income calendar view

- [ ] **Per-Alert Notification Channel Override** [LOW]
  - Choose Telegram-only, browser-only, or both on a per-alert basis

- [ ] **Alert History / Notification Log UI** [LOW]
  - Past triggered alerts with timestamp and price at trigger; accessible from Alerts page

- [ ] **Telegram Bot Webhook with `/start` Auto-Reply** [LOW]
  - Bot auto-replies to `/start` with the user's Chat ID to simplify onboarding

- [ ] **Watchlist Price Alert Shortcut** [LOW]
  - Set alert directly from watchlist row context menu; pre-fills ticker + current price

- [ ] **Portfolio Target / Goal Tracking** [LOW]
  - Set a target portfolio value or per-symbol allocation goal
  - Visual progress indicator toward goal

- [ ] **Infinite Scroll for Stock List** [LOW]
  - Replace pagination with infinite scroll + virtual list for smooth browsing

- [ ] **Drag-and-Drop Portfolio Reordering** [LOW]
  - Let users reorder holdings; persist order preference

- [ ] **Agent Report Favorites** [LOW]
  - Pin favorite AI agent reports to dashboard; quick access to frequently referenced analyses

---

## Testing

- [ ] **Snapshot Testing for UI** [LOW] — Jest snapshot tests for shared components; catch unintended UI changes in PRs
- [ ] **Mutation Testing** [LOW] — Use `mutmut` to verify test quality; identify tests that don't actually assert behavior
- [ ] **Automated Test Generation** [LOW] — Generate test templates and mock data factories for common CRUD patterns

---

## Backend

### Authentication & Security

- [ ] **OAuth2 authentication** [HIGH] — Google + GitHub sign-in via `authlib`
- [ ] **Supabase Row Level Security (RLS)** [MEDIUM] — Enable RLS on all tables once auth lands; restrict each user to their own holdings/watchlists/alerts using `auth.uid()`
- [ ] **Two-factor authentication (2FA)** [MEDIUM]
- [ ] **Role-based access control (RBAC)** [MEDIUM]
- [ ] **Session management and refresh tokens** [MEDIUM]
- [ ] **Security audit logging** [LOW]
- [ ] **API key management for third-party integrations** [LOW]

### API Enhancements

- [ ] **API rate limiting per user/IP** [MEDIUM] — Endpoint-level throttling (not just external API calls)
- [ ] **CORS Validation** [MEDIUM] — Strict allowlist of origins in production; reject unexpected preflight requests
- [ ] **API versioning strategy** [LOW] — Define v2 migration path
- [ ] **API analytics and usage tracking** [LOW]
- [ ] **GraphQL endpoint** [LOW] — Alternative to REST for flexible client queries

---

## Security

- [ ] **Security headers (CSP, HSTS, X-Frame-Options)** [HIGH] — Add via Next.js `headers()` config + FastAPI middleware
- [ ] **CSRF protection** [MEDIUM] — Double-submit cookie pattern for state-mutating endpoints
- [ ] **Input sanitization improvements** [MEDIUM]
- [ ] **XSS prevention improvements** [MEDIUM]
- [ ] **Security audit automation** [LOW] — `bandit` for Python, `npm audit` in CI
- [ ] **SQL injection prevention review** [LOW]

---

## Code Quality

- [ ] **Stricter TypeScript configurations** [MEDIUM] — Enable `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`
- [ ] **SonarQube or CodeClimate** [LOW] — Code quality and technical debt visibility
- [ ] **Automated code quality checks** [LOW]
- [ ] **Dependency vulnerability scanning** [LOW]

---

## Documentation

- [ ] **API Changelog** [MEDIUM] — Document breaking changes and new endpoints per version; keep in sync with API versioning
- [ ] **Architecture Decision Records (ADRs)** [LOW] — Document key design decisions (DB choice, async pattern, auth approach)
- [ ] **API documentation improvements (more examples)** [LOW]
- [ ] **Developer onboarding guide** [LOW]
- [ ] **Troubleshooting guides** [LOW]
- [ ] **Deployment runbooks** [LOW]

---

## How to Add Ideas

1. **Add to this file** — Every idea should be documented here
2. **Categorize** — Place in the appropriate section
3. **Prioritize** — Mark with `[HIGH]`, `[MEDIUM]`, or `[LOW]`
4. **Add context** — Include a one-line description of why it's valuable

## Priority Legend

- `[HIGH]` — High impact, should be implemented soon
- `[MEDIUM]` — Medium priority, clear value but not urgent
- `[LOW]` — Future consideration
- `[BLOCKED]` — Blocked by another dependency

---

**Last Updated**: 2026-03-21
**Open Items**: ~75
