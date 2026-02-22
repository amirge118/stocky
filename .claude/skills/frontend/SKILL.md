---
name: frontend
description: Senior-level frontend guidance for this Next.js 15 + React 19 + TypeScript stock insight app. Use when building components, pages, hooks, API integrations, or when reviewing frontend code quality.
---

# Frontend — Stock Insight App

## Stack
- **Framework:** Next.js 15 App Router (`/app` directory), React 19
- **Language:** TypeScript — strict mode, no `any`, explicit return types on exported functions
- **Styling:** Tailwind CSS v3, dark-first design (`bg-zinc-950` canvas, `bg-zinc-900` cards, `border-zinc-800`)
- **Components:** Radix UI primitives via `@/components/ui/*` — use these, never reinvent dialogs/buttons/inputs
- **Data fetching:** TanStack React Query v5 — `useQuery` / `useMutation`, no raw `fetch` in components
- **API client:** `get / post / put / del` from `@/lib/api/client.ts` — never call `fetch` directly
- **Icons:** `lucide-react` only

## File Conventions

```
frontend/
├── app/                    # Pages (App Router)
│   └── stocks/
│       ├── page.tsx        # Portfolio page (/stocks)
│       └── [symbol]/
│           └── page.tsx    # Stock detail (/stocks/AAPL)
├── components/
│   ├── features/           # Domain components (portfolio/, stocks/)
│   │   └── portfolio/
│   │       ├── PortfolioSummaryCard.tsx
│   │       ├── PortfolioTable.tsx
│   │       └── AddPositionDialog.tsx
│   ├── shared/             # Cross-domain components
│   └── ui/                 # Radix-based primitives (button, dialog, input…)
├── lib/
│   ├── api/                # One file per domain (portfolio.ts, stocks.ts)
│   ├── hooks/              # Custom React hooks
│   └── providers/          # React context providers
└── types/                  # Pure TS interfaces (portfolio.ts, stock.ts)
```

## Component Rules

```tsx
// ✅ Always: "use client" only when needed (interactivity / hooks)
// ✅ Named exports for components, default export only for pages
// ✅ Props interface above component, never inline type literals
// ✅ Co-locate sub-components in the same file if used nowhere else

"use client"

interface Props {
  symbol: string
  isPending: boolean
}

export function TickerBadge({ symbol, isPending }: Props) {
  // …
}
```

## Data Fetching Patterns

```tsx
// Query — always include queryKey that reflects all params
const { data, isPending } = useQuery({
  queryKey: ["portfolio"],            // or ["stock", symbol]
  queryFn: getPortfolio,
  refetchInterval: 60_000,            // live data refreshes
  staleTime: 30_000,
})

// Mutation — invalidate the related query on success
const mutation = useMutation({
  mutationFn: addHolding,
  onSuccess: () => queryClient.invalidateQueries({ queryKey: ["portfolio"] }),
  onError: (err: Error) => toast({ title: "Error", description: err.message, variant: "destructive" }),
})
```

## API Layer Pattern

```ts
// frontend/lib/api/portfolio.ts
import { get, post, del } from "./client"
import type { PortfolioSummary, AddHoldingRequest } from "@/types/portfolio"

export async function getPortfolio(): Promise<PortfolioSummary> {
  return get<PortfolioSummary>("/api/v1/portfolio")
}
```

## Styling Rules

### Color palette
| Token | Use |
|---|---|
| `bg-zinc-950` | Page canvas |
| `bg-zinc-900` | Cards, panels |
| `bg-zinc-800` | Table headers, hover states, inputs |
| `border-zinc-800` | Card borders |
| `text-zinc-400` | Secondary/label text |
| `text-zinc-500` | Tertiary, placeholders |
| `text-green-400` | Positive P&L, gains |
| `text-red-400` | Negative P&L, losses |
| `bg-green-400/10` | Gain badges background |
| `bg-red-400/10` | Loss badges background |

### Component shape language
- Cards: `rounded-xl border border-zinc-800 bg-zinc-900`
- Inputs: `bg-zinc-800 border-zinc-600 text-white placeholder:text-zinc-500`
- Buttons (primary): `bg-blue-600 hover:bg-blue-500 text-white`
- Buttons (ghost): `text-zinc-400 hover:text-white hover:bg-zinc-800`

### Numbers / finance data
- Always use `tabular-nums` on numeric cells
- Currency: `toLocaleString("en-US", { style: "currency", currency: "USD" })`
- Percentages: always show sign `${n >= 0 ? "+" : ""}${n.toFixed(2)}%`
- Prices: monospace font `font-mono`

## Loading / Skeleton Pattern

```tsx
if (isPending) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6 animate-pulse">
      <div className="h-5 w-32 rounded bg-zinc-700" />
    </div>
  )
}
```

## Empty State Pattern

```tsx
<div className="rounded-xl border border-zinc-800 bg-zinc-900 p-12 text-center">
  <p className="text-zinc-400">No positions yet. Add your first stock.</p>
</div>
```

## Error Handling

```tsx
// Surface API errors via toast, not thrown to the UI
onError: (err: Error) => toast({
  title: "Failed to load",
  description: err.message,
  variant: "destructive",
})
```

## Do / Don't

| Do | Don't |
|---|---|
| Use `isPending` from `useQuery` for skeleton | Use `isLoading` (deprecated in v5) |
| Pass `queryClient` from `useQueryClient()` | Import queryClient singleton |
| Use `model_dump` on the API response types | Cast with `as` |
| Invalidate queries after mutations | Manually update query cache |
| Use `router.push()` for navigation | `window.location.href` |
| Use `lucide-react` icons | Inline SVG (unless sparklines) |
| Keep page files thin — delegate to feature components | Put business logic in pages |

## Key Paths (Quick Reference)

```
Portfolio page:       frontend/app/stocks/page.tsx
Portfolio types:      frontend/types/portfolio.ts
Portfolio API:        frontend/lib/api/portfolio.ts
Portfolio components: frontend/components/features/portfolio/
Stock detail page:    frontend/app/stocks/[symbol]/page.tsx
Stock API:            frontend/lib/api/stocks.ts
API client:           frontend/lib/api/client.ts
UI primitives:        frontend/components/ui/
```
