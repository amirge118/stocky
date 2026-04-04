---
name: frontend
description: Next.js 15 + React 19 + TypeScript stock app. Use for components, pages, hooks, API integration, or frontend review.
---

# Frontend Skill — Stocky

Canonical conventions: [`frontend/.cursorrules`](../../../frontend/.cursorrules)
Full rule index: [`docs/ai/README.md`](../../../docs/ai/README.md)

---

## Think Phase (mandatory before writing any code)

Work through each item before opening an editor:

1. **Locate existing patterns** — Search `frontend/components/features/` for similar components. Never duplicate what exists.
2. **Identify data needs** — Does the data already come from an existing TanStack Query hook in `lib/hooks/`? If yes, reuse it.
3. **Server vs client component** — Default to Server Component. Add `"use client"` only when you need `useState`, `useEffect`, event handlers, or browser APIs.
4. **Caching strategy** — Pick `staleTime` based on data freshness:

   | Data type | staleTime |
   |---|---|
   | Live price / quote | 30 seconds |
   | Fundamentals (P/E, market cap) | 1 hour |
   | Historical OHLCV | `Infinity` (immutable past) |
   | AI analysis / summary | 24 hours |
   | Watchlist / portfolio (user data) | 0 (always fresh on focus) |

5. **Finance formatting** — Confirm every number uses the correct formatter:
   - Currency: `toLocaleString("en-US", { style: "currency", currency: "USD" })`
   - Percentage: `${n >= 0 ? "+" : ""}${n.toFixed(2)}%`
   - Price cells: `font-mono tabular-nums`
   - Gain color: `text-green-400 bg-green-400/10` / Loss: `text-red-400 bg-red-400/10`

6. **Chart selection**:
   - Sparkline (mini inline trend) → reuse `components/ui/Sparkline.tsx`
   - Full OHLCV candlestick / line → reuse `components/features/stocks/StockChart.tsx`
   - New chart type only if none of the above fit — use Recharts (already in deps)

7. **Plan tests** — Name the test file before writing code. Confirm you will cover: loading state, error state, success state with mock data.

---

## Act Phase

### Act 1 — Place the component

| What | Where |
|---|---|
| Stock detail sub-section | `components/features/stocks/` |
| Portfolio sub-section | `components/features/portfolio/` |
| Watchlist sub-section | `components/features/watchlist/` |
| Market / macro | `components/features/market/` |
| Reusable primitive | `components/ui/` (Shadcn-compatible) |
| Full page | `app/<route>/page.tsx` (keep thin — delegate to feature components) |

### Act 2 — Wire the API

Add a typed function to the relevant `lib/api/<domain>.ts` file. Use `get`/`post`/`put`/`del` from `@/lib/api/client.ts`. **Never call `fetch()` directly.**

```ts
// lib/api/stocks.ts
export async function getStockQuote(symbol: string): Promise<StockQuote> {
  return get<StockQuote>(`/stocks/${symbol}/quote`)
}
```

### Act 3 — Add the TanStack Query hook

Create or update a hook in `lib/hooks/use<Domain>.ts`.

```ts
// Correct v5 pattern
export function useStockQuote(symbol: string) {
  return useQuery({
    queryKey: ["stock", symbol, "quote"],
    queryFn: () => getStockQuote(symbol),
    staleTime: 30_000,   // 30s for live prices
    enabled: Boolean(symbol),
  })
}
```

### Act 4 — Implement the component

```tsx
"use client"
export function StockQuoteCard({ symbol }: { symbol: string }) {
  const { data, isPending, isError } = useStockQuote(symbol)  // isPending NOT isLoading
  if (isPending) return <Skeleton className="h-24 w-full" />
  if (isError)   return <ErrorState message="Failed to load quote" />
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
      <p className="font-mono tabular-nums text-2xl">{data.price.toLocaleString("en-US", { style: "currency", currency: "USD" })}</p>
    </div>
  )
}
```

### Act 5 — Run tests

```bash
cd frontend && npm test -- --testPathPattern="<ComponentName>"
```

### Act 6 — Update FUTURE_IMPROVEMENTS.md

Add any deferred ideas or follow-up work spotted during implementation:

```markdown
- [ ] <Idea noticed during this task> [PRIORITY]
```

---

## Critical Pitfalls

| Wrong | Right | Why |
|---|---|---|
| `isLoading` | `isPending` | TanStack Query v5 renamed it |
| `import { queryClient } from "@/lib/queryClient"` | `const queryClient = useQueryClient()` | Singleton breaks SSR hydration |
| `window.location.href = "/stocks"` | `router.push("/stocks")` from `next/navigation` | Hard navigation breaks App Router |
| `import { SomeIcon } from "react-icons/..."` | `import { SomeIcon } from "lucide-react"` | Only lucide-react is in the project |
| Hand-rolling a `<Dialog>` | `import { Dialog } from "@/components/ui/dialog"` | Shadcn primitive already exists |
| `fetch("/api/v1/stocks/...")` directly | `get<T>("/stocks/...")` from `@/lib/api/client.ts` | Bypasses auth headers and error handling |
| `className="text-green-500"` for gains | `className="text-green-400"` | Project token is `-400`, not `-500` |
