"use client"

import Link from "next/link"
import type { WatchlistItem } from "@/types/watchlist"
import type { StockData, StockEnrichedData } from "@/types/stock"

interface WatchlistHeatmapProps {
  items: WatchlistItem[]
  batchPrices: Record<string, StockData>
  enrichedMap: Record<string, StockEnrichedData>
  changePctMap: Record<string, number>
}

const MIN_PX = 72
const MAX_PX = 160

function tileColor(changePct: number | undefined): string {
  if (changePct === undefined) return "bg-zinc-800"
  const abs = Math.abs(changePct)
  if (Math.abs(changePct) < 0.05) return "bg-zinc-700"
  if (changePct > 0) {
    if (abs >= 3) return "bg-green-600"
    if (abs >= 1.5) return "bg-green-500/70"
    return "bg-green-500/40"
  } else {
    if (abs >= 3) return "bg-red-600"
    if (abs >= 1.5) return "bg-red-500/70"
    return "bg-red-500/40"
  }
}

function tileTextColor(changePct: number | undefined): string {
  if (changePct === undefined || Math.abs(changePct) < 0.05) return "text-zinc-400"
  return changePct > 0 ? "text-green-300" : "text-red-300"
}

function computeTileSizes(
  items: WatchlistItem[],
  batchPrices: Record<string, StockData>
): Record<string, number> {
  const caps: { symbol: string; logCap: number }[] = []

  for (const item of items) {
    const cap = batchPrices[item.symbol]?.market_cap
    if (cap && cap > 0) {
      caps.push({ symbol: item.symbol, logCap: Math.log10(cap) })
    }
  }

  if (caps.length === 0) {
    return Object.fromEntries(items.map((i) => [i.symbol, 96]))
  }

  const logValues = caps.map((c) => c.logCap)
  const logMin = Math.min(...logValues)
  const logMax = Math.max(...logValues)
  const range = logMax - logMin

  // Median fallback size for symbols without market cap
  const medianSize = MIN_PX + ((MAX_PX - MIN_PX) / 2)

  const sizeMap: Record<string, number> = Object.fromEntries(
    items.map((i) => [i.symbol, medianSize])
  )

  for (const { symbol, logCap } of caps) {
    const norm = range > 0 ? (logCap - logMin) / range : 0.5
    sizeMap[symbol] = Math.round(MIN_PX + norm * (MAX_PX - MIN_PX))
  }

  return sizeMap
}

export function WatchlistHeatmap({
  items,
  batchPrices,
  changePctMap,
}: WatchlistHeatmapProps) {
  const tileSizes = computeTileSizes(items, batchPrices)

  if (items.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-zinc-500 text-sm">
        No stocks in this watchlist
      </div>
    )
  }

  return (
    <div className="flex flex-wrap gap-1.5 p-1">
      {items.map((item) => {
        const size = tileSizes[item.symbol] ?? 96
        const changePct = changePctMap[item.symbol]
        const price = batchPrices[item.symbol]?.current_price

        return (
          <Link
            key={item.symbol}
            href={`/stocks/${item.symbol}`}
            title={`${item.name}${item.sector ? ` · ${item.sector}` : ""}`}
            className={`
              relative flex flex-col items-center justify-center
              rounded-md overflow-hidden cursor-pointer
              transition-opacity hover:opacity-80
              ${tileColor(changePct)}
            `}
            style={{ width: size, height: size }}
          >
            <span className="font-mono font-semibold text-white text-xs leading-tight truncate px-1 max-w-full">
              {item.symbol}
            </span>
            {changePct !== undefined && (
              <span className={`text-xs font-medium mt-0.5 ${tileTextColor(changePct)}`}>
                {changePct >= 0 ? "+" : ""}
                {changePct.toFixed(2)}%
              </span>
            )}
            {price !== undefined && (
              <span className="text-zinc-300 text-xs mt-0.5 font-mono">
                ${price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
            )}
          </Link>
        )
      })}
    </div>
  )
}
