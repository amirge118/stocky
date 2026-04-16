"use client"

import { useState, useMemo } from "react"
import { WatchlistStockRow } from "./WatchlistStockRow"
import type { WatchlistItem } from "@/types/watchlist"
import type { PriceUpdate } from "@/lib/hooks/useStockPrices"
import type { StockData, StockEnrichedData } from "@/types/stock"

type SortCol = "name" | "price" | "chg1d" | "chg1w" | "chg1m" | "volume" | "mktcap"
type SortDir = "asc" | "desc"

interface WatchlistStockListProps {
  items: WatchlistItem[]
  listId: number
  priceMap: Record<string, PriceUpdate>
  sparklineMap: Record<string, number[]>
  changePct1dMap: Record<string, number>
  changePct1wMap: Record<string, number>
  changePct1mMap: Record<string, number>
  batchPrices: Record<string, StockData>
  enrichedMap: Record<string, StockEnrichedData>
}

function SortIcon({ col, active, dir }: { col: SortCol; active: SortCol; dir: SortDir }) {
  if (col !== active) return <span className="text-zinc-700 ml-0.5">⇅</span>
  return <span className="text-zinc-300 ml-0.5">{dir === "asc" ? "▲" : "▼"}</span>
}

export function WatchlistStockList({
  items,
  listId,
  priceMap,
  sparklineMap,
  changePct1dMap,
  changePct1wMap,
  changePct1mMap,
  batchPrices,
  enrichedMap,
}: WatchlistStockListProps) {
  const [sortCol, setSortCol] = useState<SortCol>("name")
  const [sortDir, setSortDir] = useState<SortDir>("asc")

  const handleSort = (col: SortCol) => {
    if (sortCol === col) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"))
    } else {
      setSortCol(col)
      setSortDir(col === "name" ? "asc" : "desc")
    }
  }

  const sorted = useMemo(() => {
    return [...items].sort((a, b) => {
      let aVal: number | string = 0
      let bVal: number | string = 0
      switch (sortCol) {
        case "name":
          aVal = a.name?.toLowerCase() ?? a.symbol.toLowerCase()
          bVal = b.name?.toLowerCase() ?? b.symbol.toLowerCase()
          break
        case "price":
          aVal = priceMap[a.symbol]?.price ?? -Infinity
          bVal = priceMap[b.symbol]?.price ?? -Infinity
          break
        case "chg1d":
          aVal = changePct1dMap[a.symbol] ?? -Infinity
          bVal = changePct1dMap[b.symbol] ?? -Infinity
          break
        case "chg1w":
          aVal = changePct1wMap[a.symbol] ?? -Infinity
          bVal = changePct1wMap[b.symbol] ?? -Infinity
          break
        case "chg1m":
          aVal = changePct1mMap[a.symbol] ?? -Infinity
          bVal = changePct1mMap[b.symbol] ?? -Infinity
          break
        case "volume":
          aVal = batchPrices[a.symbol]?.volume ?? -Infinity
          bVal = batchPrices[b.symbol]?.volume ?? -Infinity
          break
        case "mktcap":
          aVal = batchPrices[a.symbol]?.market_cap ?? -Infinity
          bVal = batchPrices[b.symbol]?.market_cap ?? -Infinity
          break
      }
      if (typeof aVal === "string" && typeof bVal === "string") {
        return sortDir === "asc" ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal)
      }
      const n = (aVal as number) - (bVal as number)
      return sortDir === "asc" ? n : -n
    })
  }, [items, sortCol, sortDir, priceMap, changePct1dMap, changePct1wMap, changePct1mMap, batchPrices])

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
    <div>
      {/* Column headers */}
      <div className="flex items-center gap-3 px-4 py-1.5 text-xs text-zinc-600 select-none mb-1">
        <button
          onClick={() => handleSort("name")}
          className="flex-1 text-left flex items-center hover:text-zinc-400 transition-colors"
        >
          Name <SortIcon col="name" active={sortCol} dir={sortDir} />
        </button>
        <div className="shrink-0 w-20" /> {/* sparkline spacer */}
        <div className="hidden sm:flex items-center gap-1 shrink-0">
          <button
            onClick={() => handleSort("chg1d")}
            className="w-14 text-center flex items-center justify-center hover:text-zinc-400 transition-colors"
          >
            1D <SortIcon col="chg1d" active={sortCol} dir={sortDir} />
          </button>
          <button
            onClick={() => handleSort("chg1w")}
            className="w-14 text-center flex items-center justify-center hover:text-zinc-400 transition-colors"
          >
            1W <SortIcon col="chg1w" active={sortCol} dir={sortDir} />
          </button>
          <button
            onClick={() => handleSort("chg1m")}
            className="w-14 text-center flex items-center justify-center hover:text-zinc-400 transition-colors"
          >
            1M <SortIcon col="chg1m" active={sortCol} dir={sortDir} />
          </button>
          <div className="w-px mx-1" /> {/* spacer aligns with row divider */}
          <button
            onClick={() => handleSort("volume")}
            className="w-16 text-center flex items-center justify-center hover:text-zinc-400 transition-colors"
          >
            Vol <SortIcon col="volume" active={sortCol} dir={sortDir} />
          </button>
          <button
            onClick={() => handleSort("mktcap")}
            className="w-20 text-center flex items-center justify-center hover:text-zinc-400 transition-colors"
          >
            Mkt Cap <SortIcon col="mktcap" active={sortCol} dir={sortDir} />
          </button>
        </div>
        <button
          onClick={() => handleSort("price")}
          className="text-right shrink-0 w-20 flex items-center justify-end hover:text-zinc-400 transition-colors"
        >
          Price <SortIcon col="price" active={sortCol} dir={sortDir} />
        </button>
        <div className="shrink-0 w-10" /> {/* actions spacer */}
      </div>

      <div className="space-y-1">
        {sorted.map((item) => (
          <WatchlistStockRow
            key={item.id}
            item={item}
            listId={listId}
            price={priceMap[item.symbol]}
            sparkline={sparklineMap[item.symbol]}
            changePct1d={changePct1dMap[item.symbol]}
            changePct1w={changePct1wMap[item.symbol]}
            changePct1m={changePct1mMap[item.symbol]}
            volume={batchPrices[item.symbol]?.volume ?? undefined}
            marketCap={batchPrices[item.symbol]?.market_cap ?? undefined}
            enriched={enrichedMap[item.symbol]}
          />
        ))}
      </div>
    </div>
  )
}
