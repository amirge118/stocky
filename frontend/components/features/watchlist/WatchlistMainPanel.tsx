"use client"

import { useState } from "react"
import { useQuery, useQueries } from "@tanstack/react-query"
import { getWatchlist, getWatchlists } from "@/lib/api/watchlists"
import { fetchStockDataBatch, getStockHistory } from "@/lib/api/stocks"
import { useStockPrices } from "@/lib/hooks/useStockPrices"
import { WatchlistStockList } from "./WatchlistStockList"
import { WatchlistAddStockDialog } from "./WatchlistAddStockDialog"
import { Button } from "@/components/ui/button"
import type { WatchlistItem } from "@/types/watchlist"

interface WatchlistMainPanelProps {
  activeListId: number | null
}

export function WatchlistMainPanel({ activeListId }: WatchlistMainPanelProps) {
  const [addOpen, setAddOpen] = useState(false)

  // "All" view: fetch all lists, then each individual list
  const { data: summaries } = useQuery({
    queryKey: ["watchlists"],
    queryFn: getWatchlists,
  })

  const allListIds = summaries?.map((s) => s.id) ?? []

  // Fetch individual lists for "All" view
  const listQueries = useQueries({
    queries: allListIds.map((id) => ({
      queryKey: ["watchlists", id] as const,
      queryFn: () => getWatchlist(id),
      enabled: activeListId === null,
    })),
  })

  // Fetch the active list
  const { data: activeList } = useQuery({
    queryKey: ["watchlists", activeListId!],
    queryFn: () => getWatchlist(activeListId!),
    enabled: activeListId !== null,
  })

  // Derive items to display
  let displayItems: WatchlistItem[] = []
  let displayName = "All"
  let displayListId = -1

  if (activeListId !== null) {
    displayItems = activeList?.items ?? []
    displayName = activeList?.name ?? ""
    displayListId = activeListId
  } else {
    // Deduplicate by symbol across all lists
    const seen = new Set<string>()
    for (const q of listQueries) {
      if (q.data) {
        for (const item of q.data.items) {
          if (!seen.has(item.symbol)) {
            seen.add(item.symbol)
            displayItems.push(item)
          }
        }
      }
    }
  }

  const symbols = displayItems.map((i) => i.symbol)

  // Batch fetch initial prices
  const { data: batchPrices } = useQuery({
    queryKey: ["stockData", symbols.join(",")],
    queryFn: () => fetchStockDataBatch(symbols),
    enabled: symbols.length > 0,
    staleTime: 30_000,
  })

  // WebSocket live prices
  const wsPrices = useStockPrices(symbols)

  // Merge: WS prices override batch prices
  const priceMap = Object.fromEntries(
    symbols.map((sym) => {
      if (wsPrices[sym]) return [sym, wsPrices[sym]]
      const batch = batchPrices?.[sym]
      if (batch) {
        return [
          sym,
          {
            symbol: sym,
            price: batch.current_price ?? 0,
            change: batch.change ?? 0,
            change_percent: batch.change_percent ?? 0,
          },
        ]
      }
      return [sym, undefined]
    })
  ) as Record<string, import("@/lib/hooks/useStockPrices").PriceUpdate>

  // Sparklines
  const sparklineQueries = useQueries({
    queries: symbols.map((sym) => ({
      queryKey: ["stockHistory", sym, "1w"] as const,
      queryFn: () => getStockHistory(sym, "1w"),
      staleTime: 5 * 60_000,
    })),
  })

  const sparklineMap: Record<string, number[]> = {}
  symbols.forEach((sym, idx) => {
    const history = sparklineQueries[idx]?.data
    if (history?.data) {
      sparklineMap[sym] = history.data.map((p) => p.c)
    }
  })

  const isLoading =
    activeListId !== null
      ? !activeList
      : listQueries.some((q) => q.isLoading)

  const activeListSummary = summaries?.find((s) => s.id === activeListId)

  return (
    <main className="flex-1 min-w-0 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-white">
            {displayName}
            <span className="ml-2 text-sm font-normal text-zinc-500">
              ({displayItems.length})
            </span>
          </h1>
        </div>
        {activeListId !== null && (
          <Button
            size="sm"
            onClick={() => setAddOpen(true)}
            className="bg-zinc-700 hover:bg-zinc-600 text-white border-0"
          >
            + Add Stock
          </Button>
        )}
      </div>

      {/* Divider */}
      <div className="border-t border-zinc-800 mb-4" />

      {/* Stock list */}
      {isLoading ? (
        <div className="space-y-2">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-16 rounded-lg bg-zinc-800/50 animate-pulse" />
          ))}
        </div>
      ) : (
        <WatchlistStockList
          items={displayItems}
          listId={displayListId}
          priceMap={priceMap}
          sparklineMap={sparklineMap}
        />
      )}

      {/* Add stock dialog */}
      {activeListId !== null && (
        <WatchlistAddStockDialog
          open={addOpen}
          listId={activeListId}
          listName={activeListSummary?.name ?? displayName}
          onOpenChange={setAddOpen}
        />
      )}
    </main>
  )
}
