---
name: stock-feature
description: Full-stack feature build for Stocky. Enforces backend-first, API-first layer ordering across FastAPI + Next.js. Use for any new end-to-end feature.
---

# Stock Feature Skill — Stocky

Use this skill for any feature that spans backend + frontend (new endpoint + new component).

Canonical conventions:
- Backend: [`backend/.cursorrules`](../../../backend/.cursorrules)
- Frontend: [`frontend/.cursorrules`](../../../frontend/.cursorrules)
- API design: [`.cursor/rules/api-design-rules.md`](../../../.cursor/rules/api-design-rules.md)

---

## Think Phase (mandatory — plan all 7 layers before writing anything)

### Think 1: Check existing services first

Before building anything new, check whether the data already exists:

| Service | Provides |
|---|---|
| `backend/app/services/stock_service.py` | Core stock lookup, metadata |
| `backend/app/services/yfinance_service.py` | Price history, OHLCV, fundamentals |
| `backend/app/services/market_service.py` | Market-wide data, indices, movers |
| `backend/app/services/watchlist_service.py` | User watchlist CRUD |
| `backend/app/services/alert_service.py` | Price alert CRUD and evaluation |
| `backend/app/services/holding_service.py` | Portfolio holdings CRUD |
| `backend/app/services/price_service.py` | Live price fetching / caching |

If the data exists in a service, add an endpoint — do NOT create a duplicate service.

### Think 2: Caching strategy

| Data type | Backend cache TTL | Frontend staleTime |
|---|---|---|
| Live quote / price | 30s | 30s |
| Fundamentals (P/E, market cap) | 1h | 1h |
| Historical OHLCV | 24h | `Infinity` |
| AI analysis / summary | 24h | 24h |
| User data (portfolio, watchlist) | None (always DB) | 0 |

### Think 3: API contract

Define before writing code:
- URL: `GET /api/v1/<resource>/<id>/<sub-resource>`
- Request body / query params (Pydantic schema name)
- Response schema (Pydantic schema name)
- Error cases: 404 for unknown symbol, 422 for bad params, 503 if yfinance unavailable

### Think 4: Map all 7 files

Write these file paths before touching any of them:

```
backend/app/schemas/<domain>.py          # 1. Pydantic schema
backend/app/services/<domain>_service.py # 2. Service function
backend/app/api/v1/endpoints/<domain>.py # 3. FastAPI endpoint
backend/tests/unit/test_<domain>_service.py     # 4. Backend unit tests
backend/tests/integration/test_<domain>_api.py  # 5. Backend integration tests
frontend/lib/api/<domain>.ts             # 6. Frontend API client
frontend/components/features/<domain>/   # 7. React component(s)
```

### Think 5: Edge cases to handle

- **Invalid symbol** → 404 (not 500)
- **yfinance returns empty DataFrame** → 404 with `detail: "No data available for {symbol}"`
- **yfinance network error** → 503 with `detail: "Market data unavailable"`
- **AI timeout** → return partial result or 504, never hang indefinitely
- **Empty portfolio** → empty array `[]`, not 404

---

## Act Phase

### Act 1 — Pydantic schemas (`backend/app/schemas/<domain>.py`)

```python
from pydantic import BaseModel, Field
from datetime import datetime

class DividendEntry(BaseModel):
    date: datetime
    amount: float = Field(..., description="Dividend per share in USD")

class DividendHistoryResponse(BaseModel):
    symbol: str
    dividends: list[DividendEntry]
```

### Act 2 — Service function (`backend/app/services/<domain>_service.py`)

```python
async def get_dividend_history(symbol: str) -> list[DividendEntry]:
    df = await yfinance_service.get_dividends(symbol)  # raises HTTPException on error
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No dividend data for {symbol}")
    return [DividendEntry(date=d, amount=v) for d, v in df.items()]
```

### Act 3 — FastAPI endpoint (`backend/app/api/v1/endpoints/<domain>.py`)

```python
@router.get("/{symbol}/dividends", response_model=DividendHistoryResponse)
async def get_dividends(symbol: str = Path(..., min_length=1, max_length=10)):
    dividends = await dividend_service.get_dividend_history(symbol.upper())
    return DividendHistoryResponse(symbol=symbol.upper(), dividends=dividends)
```

Register in `backend/app/api/v1/router.py` if adding a new router.

### Act 4 — Backend tests

**Unit test** (`backend/tests/unit/test_<domain>_service.py`):
```python
@pytest.mark.asyncio
async def test_get_dividend_history_empty_symbol(mock_yfinance):
    mock_yfinance.get_dividends.return_value = pd.DataFrame()
    with pytest.raises(HTTPException) as exc:
        await get_dividend_history("FAKE")
    assert exc.value.status_code == 404
```

**Integration test** (`backend/tests/integration/test_<domain>_api.py`):
```python
@pytest.mark.asyncio
async def test_dividends_endpoint(async_client, mock_yfinance):
    mock_yfinance.get_dividends.return_value = sample_dividend_df
    response = await async_client.get("/api/v1/stocks/AAPL/dividends")
    assert response.status_code == 200
    assert response.json()["symbol"] == "AAPL"
```

### Act 5 — Frontend API client (`frontend/lib/api/<domain>.ts`)

```ts
import { get } from "@/lib/api/client"
import type { DividendHistoryResponse } from "@/types/stock"

export async function getDividendHistory(symbol: string): Promise<DividendHistoryResponse> {
  return get<DividendHistoryResponse>(`/stocks/${symbol}/dividends`)
}
```

Add the TypeScript type to `frontend/types/stock.ts` (or appropriate types file).

### Act 6 — React component (`frontend/components/features/stocks/`)

```tsx
"use client"
import { useQuery } from "@tanstack/react-query"
import { getDividendHistory } from "@/lib/api/stocks"

export function DividendHistorySection({ symbol }: { symbol: string }) {
  const { data, isPending, isError } = useQuery({  // isPending NOT isLoading
    queryKey: ["stock", symbol, "dividends"],
    queryFn: () => getDividendHistory(symbol),
    staleTime: 24 * 60 * 60 * 1000,  // 24h — historical data
  })

  if (isPending) return <Skeleton className="h-32 w-full" />
  if (isError)   return <ErrorState message="Failed to load dividend history" />

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
      {/* render data.dividends */}
    </div>
  )
}
```

### Act 7 — Frontend tests

```bash
cd frontend && npm test -- --testPathPattern="DividendHistory"
```

Cover: `isPending` skeleton, error state, success state with mock data.

### Act 8 — Update FUTURE_IMPROVEMENTS.md

```markdown
- [ ] <Any deferred idea spotted during this feature> [PRIORITY]
```

Never skip this step.

### Act 9 — Verify full stack

```bash
# Backend
cd backend && pytest tests/unit/test_<domain>_service.py tests/integration/test_<domain>_api.py -v

# Frontend
cd frontend && npm test -- --testPathPattern="<ComponentName>"

# Manual smoke test
curl http://localhost:8000/api/v1/stocks/AAPL/dividends
```

---

## Common Mistakes

| Wrong | Right |
|---|---|
| Creating a new service when one already covers the data | Check Think 1 table first |
| `raise Exception(...)` in service | `raise HTTPException(status_code=..., detail=...)` |
| `isLoading` in TanStack Query | `isPending` (v5) |
| `fetch(...)` in component | `get<T>(...)` from `@/lib/api/client.ts` |
| Returning 500 when yfinance has no data | Return 404 — no data is not a server error |
| Skipping FUTURE_IMPROVEMENTS.md | Act 8 is mandatory |
