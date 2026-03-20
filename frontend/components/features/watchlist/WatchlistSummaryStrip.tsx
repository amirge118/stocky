"use client"

import type { StockData } from "@/types/stock"

interface WatchlistSummaryStripProps {
  prices: Record<string, StockData | undefined>
  symbols: string[]
}

export function WatchlistSummaryStrip({ prices, symbols }: WatchlistSummaryStripProps) {
  if (symbols.length === 0) return null

  let gainers = 0
  let losers = 0
  let flat = 0
  let best: { symbol: string; pct: number } | null = null
  let worst: { symbol: string; pct: number } | null = null
  let sum = 0
  let count = 0

  for (const sym of symbols) {
    const d = prices[sym]
    if (!d) continue
    const pct = d.change_percent ?? 0
    sum += pct
    count++
    if (pct > 0.05) gainers++
    else if (pct < -0.05) losers++
    else flat++
    if (best === null || pct > best.pct) best = { symbol: sym, pct }
    if (worst === null || pct < worst.pct) worst = { symbol: sym, pct }
  }

  const avg = count > 0 ? sum / count : null

  const fmtPct = (v: number) => `${v >= 0 ? "+" : ""}${v.toFixed(2)}%`

  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 px-4 py-2.5 rounded-lg bg-zinc-900/70 border border-zinc-800 text-xs mb-4">
      {/* Gainers / Losers / Flat */}
      <span className="text-green-400 font-medium">↑ {gainers} Gainer{gainers !== 1 ? "s" : ""}</span>
      <span className="text-zinc-600">|</span>
      <span className="text-red-400 font-medium">↓ {losers} Loser{losers !== 1 ? "s" : ""}</span>
      <span className="text-zinc-600">|</span>
      <span className="text-zinc-500">— {flat} Flat</span>

      <span className="text-zinc-700 hidden sm:block">|</span>

      {/* Best */}
      <span className="hidden sm:flex items-center gap-1 text-zinc-400">
        Best:
        {best ? (
          <>
            <span className="font-mono text-zinc-200">{best.symbol}</span>
            <span className="text-green-400 font-medium">{fmtPct(best.pct)}</span>
          </>
        ) : (
          <span className="text-zinc-600">—</span>
        )}
      </span>

      {/* Worst */}
      <span className="hidden sm:flex items-center gap-1 text-zinc-400">
        Worst:
        {worst ? (
          <>
            <span className="font-mono text-zinc-200">{worst.symbol}</span>
            <span className="text-red-400 font-medium">{fmtPct(worst.pct)}</span>
          </>
        ) : (
          <span className="text-zinc-600">—</span>
        )}
      </span>

      <span className="text-zinc-700 hidden sm:block">|</span>

      {/* Average */}
      <span className="hidden sm:flex items-center gap-1 text-zinc-400">
        Avg:
        {avg !== null ? (
          <span className={avg >= 0 ? "text-green-400 font-medium" : "text-red-400 font-medium"}>
            {fmtPct(avg)}
          </span>
        ) : (
          <span className="text-zinc-600">—</span>
        )}
      </span>
    </div>
  )
}
