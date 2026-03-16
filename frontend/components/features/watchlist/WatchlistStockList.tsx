"use client"

import { WatchlistStockRow } from "./WatchlistStockRow"
import type { WatchlistItem } from "@/types/watchlist"
import type { PriceUpdate } from "@/lib/hooks/useStockPrices"

interface WatchlistStockListProps {
  items: WatchlistItem[]
  listId: number
  priceMap: Record<string, PriceUpdate>
  sparklineMap: Record<string, number[]>
}

export function WatchlistStockList({
  items,
  listId,
  priceMap,
  sparklineMap,
}: WatchlistStockListProps) {
  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-zinc-600">
        <span className="text-3xl mb-3">📋</span>
        <p className="text-sm">No stocks yet.</p>
        <p className="text-xs mt-1">Use &ldquo;+ Add Stock&rdquo; to start tracking.</p>
      </div>
    )
  }

  return (
    <div className="space-y-1">
      {items.map((item) => (
        <WatchlistStockRow
          key={item.id}
          item={item}
          listId={listId}
          price={priceMap[item.symbol]}
          sparkline={sparklineMap[item.symbol]}
        />
      ))}
    </div>
  )
}
