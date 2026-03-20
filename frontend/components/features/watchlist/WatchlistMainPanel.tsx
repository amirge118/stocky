"use client"

import { useState } from "react"
import { useQuery, useQueries } from "@tanstack/react-query"
import { getWatchlist, getWatchlists } from "@/lib/api/watchlists"
import { fetchStockDataBatch, getStockHistory, fetchStockEnrichedBatch } from "@/lib/api/stocks"
import { useStockPrices } from "@/lib/hooks/useStockPrices"
import { WatchlistStockList } from "./WatchlistStockList"
import { WatchlistAddStockDialog } from "./WatchlistAddStockDialog"
import { WatchlistSummaryStrip } from "./WatchlistSummaryStrip"
import { Button } from "@/components/ui/button"
import type { WatchlistItem } from "@/types/watchlist"
import type { StockData, StockEnrichedData } from "@/types/stock"

type Period = "1d" | "1w" | "1m"

interface WatchlistMainPanelProps {
  activeListId: number | null
}

export function WatchlistMainPanel({ activeListId }: WatchlistMainPanelProps) {
  const [addOpen, setAddOpen] = useState(false)
  const [period, setPeriod] = useState<Period>("1w")

  // "All" view: fetch all lists, then each individual list
  const { data: summaries, isError: summariesError } = useQuery({
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

  // Sparklines — parameterised by period
  const sparklineQueries = useQueries({
    queries: symbols.map((sym) => ({
      queryKey: ["stockHistory", sym, period] as const,
      queryFn: () => getStockHistory(sym, period),
      staleTime: 5 * 60_000,
    })),
  })

  const sparklineMap: Record<string, number[]> = {}
  const periodChangeMap: Record<string, number> = {}

  symbols.forEach((sym, idx) => {
    const history = sparklineQueries[idx]?.data
    if (history?.data && history.data.length >= 2) {
      const closes = history.data.map((p) => p.c)
      sparklineMap[sym] = closes
      if (period !== "1d") {
        const first = closes[0]
        const last = closes[closes.length - 1]
        if (first > 0) periodChangeMap[sym] = ((last - first) / first) * 100
      }
    }
    // For 1d, use batch price change_percent
    if (period === "1d" && batchPrices?.[sym]?.change_percent != null) {
      periodChangeMap[sym] = batchPrices[sym].change_percent
    }
  })

  // Enriched data — slow-changing, cached 1hr
  const { data: enrichedRaw } = useQuery({
    queryKey: ["stockEnriched", symbols.join(",")],
    queryFn: () => fetchStockEnrichedBatch(symbols),
    enabled: symbols.length > 0,
    staleTime: 3_600_000,
  })
  const enrichedMap: Record<string, StockEnrichedData> = enrichedRaw ?? {}

  // Summary strip price map — uses batchPrices (StockData shape)
  const summaryPrices: Record<string, StockData | undefined> = Object.fromEntries(
    symbols.map((sym) => [sym, batchPrices?.[sym]])
  )

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
        <div className="flex items-center gap-2">
          {/* Period toggle */}
          <div className="flex rounded-md border border-zinc-700 overflow-hidden text-xs">
            {(["1d", "1w", "1m"] as Period[]).map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={`px-2.5 py-1 font-mono uppercase transition-colors ${
                  period === p
                    ? "bg-zinc-700 text-white"
                    : "bg-transparent text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800"
                }`}
              >
                {p}
              </button>
            ))}
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
      </div>

      {/* Divider */}
      <div className="border-t border-zinc-800 mb-4" />

      {/* Summary strip */}
      {!isLoading && symbols.length > 0 && (
        <WatchlistSummaryStrip prices={summaryPrices} symbols={symbols} />
      )}

      {/* Error state */}
      {summariesError && (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 px-5 py-4 text-sm text-zinc-400 mb-4">
          Failed to load watchlist data. Check your connection.
        </div>
      )}

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
          changePctMap={periodChangeMap}
          batchPrices={batchPrices ?? {}}
          period={period}
          enrichedMap={enrichedMap}
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
