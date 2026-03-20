"use client"

import Link from "next/link"
import { useQuery, useQueries } from "@tanstack/react-query"
import { getPortfolio } from "@/lib/api/portfolio"
import { getWatchlists, getWatchlist } from "@/lib/api/watchlists"
import { fetchStockDataBatch } from "@/lib/api/stocks"
import type { StockData } from "@/types/stock"

interface MoverRowProps {
  symbol: string
  data: StockData
}

function MoverRow({ symbol, data }: MoverRowProps) {
  const isPositive = data.change_percent >= 0
  const changeColor = isPositive ? "text-green-400" : "text-red-400"
  const sign = isPositive ? "+" : ""

  return (
    <Link
      href={`/stocks/${symbol}`}
      className="flex items-center justify-between py-2 px-3 rounded-md hover:bg-zinc-800 transition-colors group"
    >
      <div className="flex flex-col min-w-0">
        <span className="text-sm font-semibold text-white group-hover:text-zinc-200">
          {symbol}
        </span>
        <span className="text-xs text-zinc-500 truncate">{data.name || symbol}</span>
      </div>
      <div className="flex flex-col items-end shrink-0">
        <span className="text-sm font-medium text-zinc-200 tabular-nums">
          ${data.current_price.toFixed(2)}
        </span>
        <span className={`text-xs font-semibold tabular-nums ${changeColor}`}>
          {sign}{data.change_percent.toFixed(2)}%
        </span>
      </div>
    </Link>
  )
}

export function YourMovers() {
  const { data: portfolio } = useQuery({
    queryKey: ["portfolio"],
    queryFn: getPortfolio,
    staleTime: 5 * 60 * 1000,
  })

  const { data: watchlistSummaries = [] } = useQuery({
    queryKey: ["watchlists"],
    queryFn: getWatchlists,
    staleTime: 5 * 60 * 1000,
  })

  const watchlistQueries = useQueries({
    queries: watchlistSummaries.map((s) => ({
      queryKey: ["watchlist", s.id],
      queryFn: () => getWatchlist(s.id),
      staleTime: 5 * 60 * 1000,
    })),
  })

  // Collect all symbols from portfolio + watchlists, deduplicated
  const symbols = Array.from(
    new Set([
      ...(portfolio?.positions.map((p) => p.symbol) ?? []),
      ...watchlistQueries
        .flatMap((q) => q.data?.items.map((i) => i.symbol) ?? []),
    ])
  )

  const symbolsKey = symbols.slice().sort().join(",")

  const { data: priceMap } = useQuery({
    queryKey: ["stockBatch", symbolsKey],
    queryFn: () => fetchStockDataBatch(symbols),
    enabled: symbols.length > 0,
    staleTime: 5 * 60 * 1000,
  })

  const movers = Object.entries(priceMap ?? {})
    .sort((a, b) => Math.abs(b[1].change_percent) - Math.abs(a[1].change_percent))
    .slice(0, 6)

  const hasData = symbols.length > 0

  return (
    <section className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
      <h2 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-3">
        Your Movers
      </h2>
      {!hasData && (
        <p className="text-sm text-zinc-500 px-3 py-4 text-center">
          Add stocks to your portfolio or watchlist to see your movers.
        </p>
      )}
      {hasData && movers.length === 0 && (
        <p className="text-sm text-zinc-500 px-3 py-4 text-center">Loading...</p>
      )}
      <div className="space-y-0.5">
        {movers.map(([symbol, data]) => (
          <MoverRow key={symbol} symbol={symbol} data={data} />
        ))}
      </div>
    </section>
  )
}
