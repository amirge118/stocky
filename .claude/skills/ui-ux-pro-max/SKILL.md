---
name: ui-ux-pro-max
description: Professional UI/UX design system for Stocky. Wraps the Python design-system search tool with Stocky-specific dark theme overrides and fintech chart guidance.
---

# UI/UX Pro Max — Stocky

Wraps the comprehensive design system at `.cursor/skills/ui-ux-pro-max/` for Claude Code use.
The system contains: 67 styles, 96 color palettes, 57 font pairings, 99 UX guidelines, 25 chart types.

> **Stocky theme overrides always win.** If design system output conflicts with the tokens below, use the Stocky tokens.

## Stocky Dark Theme Tokens (authoritative)

| Token | Tailwind class | Use |
|---|---|---|
| Page canvas | `bg-zinc-950` | Root / layout background |
| Cards & panels | `bg-zinc-900` | All card surfaces |
| Table headers / inputs / hover | `bg-zinc-800` | Secondary surfaces |
| Card borders | `border-zinc-800` | All card outlines |
| Secondary text / labels | `text-zinc-400` | Supporting copy |
| Gain | `text-green-400` + `bg-green-400/10` | Positive delta, badges |
| Loss | `text-red-400` + `bg-red-400/10` | Negative delta, badges |
| Card shell | `rounded-xl border border-zinc-800 bg-zinc-900` | Standard card pattern |

Icons: `lucide-react` only. No emojis as icons.

---

## Prerequisites

```bash
python3 --version  # must be 3.8+
```

---

## Step 1: Analyze Requirements

Extract from the user request:
- **Component type**: card, table, chart, badge, modal, page, etc.
- **Data domain**: stock quote, portfolio, watchlist, market pulse, alerts
- **Style keywords**: professional, dark, fintech, dense data, clean

---

## Step 2: Generate Design System

Always start with `--design-system`. Run from the **repo root**:

```bash
python3 .cursor/skills/ui-ux-pro-max/scripts/search.py "fintech stock dashboard dark professional" --design-system -p "Stocky" -f markdown
```

The script searches 5 domains in parallel and returns: pattern, style, colors, typography, effects, anti-patterns.

**Persist for session reuse:**
```bash
python3 .cursor/skills/ui-ux-pro-max/scripts/search.py "fintech stock dashboard dark professional" --design-system --persist -p "Stocky"
```

---

## Step 3: Supplement with Domain Searches

```bash
# Chart recommendations for stock data
python3 .cursor/skills/ui-ux-pro-max/scripts/search.py "real-time financial data trend comparison" --domain chart

# UX guidelines (animation, accessibility)
python3 .cursor/skills/ui-ux-pro-max/scripts/search.py "animation accessibility keyboard dense-data" --domain ux

# Next.js-specific performance patterns
python3 .cursor/skills/ui-ux-pro-max/scripts/search.py "suspense streaming cache waterfall" --stack nextjs
```

---

## Chart Type Quick Reference (Stocky)

| Data | Existing component | When to add new |
|---|---|---|
| Mini price trend (inline) | `components/ui/Sparkline.tsx` | Never — reuse |
| Full price history / OHLCV | `components/features/stocks/StockChart.tsx` | Only for new chart type |
| Portfolio performance over time | `components/features/portfolio/PortfolioPerformanceChart.tsx` | Only for new metric |
| Distribution / allocation | None — use Recharts `PieChart` | Always available via Recharts |
| Comparison bar | None — use Recharts `BarChart` | Always available via Recharts |

Recharts is already installed. Do not add Chart.js, D3, or other charting libraries without explicit approval.

---

## Fintech-Specific UX Rules

1. **Numeric alignment**: price/quantity columns → `font-mono tabular-nums text-right`
2. **Color semantics**: green = positive return, red = negative — never use these colors for non-financial meaning
3. **Loading states**: use `Skeleton` from `@/components/ui/skeleton`, not spinners, for data tables
4. **Error states**: show last-known value with a stale indicator rather than hiding data entirely
5. **Density**: financial dashboards are data-dense by design — don't add excessive whitespace
6. **Tooltips on charts**: always show exact value + timestamp on hover (Recharts `<Tooltip>`)

---

## Pre-Delivery Checklist

- [ ] All Stocky dark tokens used (no hardcoded hex colors)
- [ ] No emojis as icons — only `lucide-react`
- [ ] Price/delta values formatted with correct finance formatters
- [ ] Gain/loss always colored `text-green-400` / `text-red-400`
- [ ] Numeric columns: `font-mono tabular-nums`
- [ ] All clickable elements: `cursor-pointer`
- [ ] Hover transitions: `transition-colors duration-200`
- [ ] Skeleton shown during `isPending`, error UI on `isError`
- [ ] Responsive at 375px, 768px, 1024px, 1440px
