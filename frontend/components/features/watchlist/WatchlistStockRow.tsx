"use client"

import { useState } from "react"
import Link from "next/link"
import { Bell } from "lucide-react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { removeItemFromWatchlist } from "@/lib/api/watchlists"
import { Sparkline } from "@/components/features/stocks/Sparkline"
import { AlertDialog } from "@/components/features/stocks/AlertDialog"
import type { WatchlistItem, WatchlistListResponse, WatchlistListSummary } from "@/types/watchlist"
import type { PriceUpdate } from "@/lib/hooks/useStockPrices"
import type { StockEnrichedData } from "@/types/stock"
import { usePriceFlash } from "@/lib/hooks/usePriceFlash"

interface WatchlistStockRowProps {
  item: WatchlistItem
  listId: number
  price: PriceUpdate | undefined
  sparkline: number[] | undefined
  changePct1d: number | undefined
  changePct1w: number | undefined
  changePct1m: number | undefined
  volume: number | undefined
  marketCap: number | undefined
  enriched: StockEnrichedData | undefined
}

function formatVolume(v: number): string {
  if (v >= 1_000_000_000) return `${(v / 1_000_000_000).toFixed(1)}B`
  if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`
  if (v >= 1_000) return `${(v / 1_000).toFixed(0)}K`
  return v.toString()
}

function formatMarketCap(v: number): string {
  if (v >= 1_000_000_000_000) return `${(v / 1_000_000_000_000).toFixed(2)}T`
  if (v >= 1_000_000_000) return `${(v / 1_000_000_000).toFixed(2)}B`
  if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`
  return `${v.toFixed(0)}`
}

function AnalystBadge({ rating }: { rating: string | null | undefined }) {
  if (!rating) return null
  const map: Record<string, { label: string; cls: string }> = {
    strong_buy: { label: "STRONG BUY", cls: "bg-green-500/20 text-green-400 border-green-500/30" },
    buy: { label: "BUY", cls: "bg-green-500/20 text-green-400 border-green-500/30" },
    hold: { label: "HOLD", cls: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30" },
    sell: { label: "SELL", cls: "bg-red-500/20 text-red-400 border-red-500/30" },
    underperform: { label: "SELL", cls: "bg-red-500/20 text-red-400 border-red-500/30" },
  }
  const entry = map[rating.toLowerCase()]
  if (!entry) return null
  return (
    <span className={`text-xs font-semibold px-1.5 py-0.5 rounded border ${entry.cls}`}>
      {entry.label}
    </span>
  )
}

function RelVolBadge({ volume, avgVolume }: { volume: number | undefined; avgVolume: number | null | undefined }) {
  if (!volume || !avgVolume || avgVolume <= 0) return null
  const ratio = volume / avgVolume
  if (ratio >= 0.7 && ratio < 1.5) return null

  if (ratio < 0.7) {
    return (
      <span className="text-xs font-medium px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">
        Low Vol
      </span>
    )
  }
  const label = ratio.toFixed(1) + "×"
  if (ratio >= 2) {
    return (
      <span className="text-xs font-medium px-1.5 py-0.5 rounded bg-red-500/20 text-red-400 border border-red-500/30">
        {label}
      </span>
    )
  }
  return (
    <span className="text-xs font-medium px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-400 border border-amber-500/30">
      {label}
    </span>
  )
}

function FiftyTwoWeekBar({
  price,
  low,
  high,
}: {
  price: number | undefined
  low: number | null | undefined
  high: number | null | undefined
}) {
  if (!price || !low || !high || high <= low) return null
  const pct = Math.min(100, Math.max(0, ((price - low) / (high - low)) * 100))
  return (
    <div className="mt-1 w-full" title={`52W Low $${low.toFixed(2)} — High $${high.toFixed(2)}`}>
      <div className="relative h-1 rounded-full bg-zinc-700/60 overflow-visible">
        <div
          className="absolute inset-y-0 left-0 bg-green-500/50 rounded-full"
          style={{ width: `${pct}%` }}
        />
        <div
          className="absolute top-1/2 -translate-y-1/2 w-2 h-2 rounded-full bg-green-400 border border-zinc-900 shadow"
          style={{ left: `calc(${pct}% - 4px)` }}
        />
      </div>
    </div>
  )
}

function ChangePctCell({ value, label }: { value: number | undefined; label: string }) {
  return (
    <div className="text-center w-14">
      <div className="text-[10px] text-zinc-600 mb-0.5 font-mono uppercase">{label}</div>
      {value != null ? (
        <div className={`text-xs font-mono tabular-nums font-medium ${value >= 0 ? "text-green-400" : "text-red-400"}`}>
          {value >= 0 ? "+" : ""}{value.toFixed(2)}%
        </div>
      ) : (
        <div className="text-xs text-zinc-700">—</div>
      )}
    </div>
  )
}

export function WatchlistStockRow({
  item,
  listId,
  price,
  sparkline,
  changePct1d,
  changePct1w,
  changePct1m,
  volume,
  marketCap,
  enriched,
}: WatchlistStockRowProps) {
  const queryClient = useQueryClient()
  const [alertOpen, setAlertOpen] = useState(false)

  const removeMutation = useMutation({
    mutationFn: () => removeItemFromWatchlist(listId, item.symbol),
    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey: ["watchlists", listId] })
      const prev = queryClient.getQueryData<WatchlistListResponse>(["watchlists", listId])
      queryClient.setQueryData<WatchlistListResponse>(["watchlists", listId], (old) =>
        old ? { ...old, items: old.items.filter((i) => i.id !== item.id) } : old
      )
      queryClient.setQueryData<WatchlistListSummary[]>(["watchlists"], (old) =>
        old?.map((l) =>
          l.id === listId ? { ...l, item_count: Math.max(0, l.item_count - 1) } : l
        )
      )
      return { prev }
    },
    onError: (_err, _vars, ctx) => {
      if (ctx?.prev) queryClient.setQueryData(["watchlists", listId], ctx.prev)
      queryClient.invalidateQueries({ queryKey: ["watchlists"] })
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["watchlists", listId] })
      queryClient.invalidateQueries({ queryKey: ["watchlists"] })
    },
  })

  const displayPrice = price?.price
  const flashClass = usePriceFlash(displayPrice)

  return (
    <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-zinc-900 hover:bg-zinc-800/50 transition-colors">
      {/* Symbol + name */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <Link
            href={`/stocks/${item.symbol}`}
            className="font-mono font-semibold text-sm text-zinc-100 hover:text-white border border-zinc-700 rounded px-1.5 py-0.5 hover:border-zinc-500 transition-colors"
          >
            {item.symbol}
          </Link>
          <span className="text-sm text-zinc-300 truncate">{item.name}</span>
          <AnalystBadge rating={enriched?.analyst_rating} />
        </div>
        {item.sector && (
          <span className="text-xs text-zinc-600 mt-0.5 block">{item.sector}</span>
        )}
      </div>

      {/* Sparkline — always 1D shape */}
      <div className="shrink-0">
        {sparkline && sparkline.length >= 2 ? (
          <Sparkline data={sparkline} width={80} height={28} />
        ) : (
          <div className="w-20 h-7 bg-zinc-800/50 rounded skeleton-shimmer" />
        )}
      </div>

      {/* Period columns: 1D | 1W | 1M */}
      <div className="hidden sm:flex items-center gap-1 shrink-0">
        <ChangePctCell value={changePct1d} label="1D" />
        <ChangePctCell value={changePct1w} label="1W" />
        <ChangePctCell value={changePct1m} label="1M" />

        {/* Divider */}
        <div className="w-px h-8 bg-zinc-800 mx-1 shrink-0" />

        {/* Vol */}
        <div className="text-center w-16">
          <div className="text-[10px] text-zinc-600 mb-0.5 font-mono uppercase">Vol</div>
          {volume != null ? (
            <div className="flex flex-col items-center gap-0.5">
              <div className="text-xs font-mono tabular-nums text-zinc-400">
                {formatVolume(volume)}
              </div>
              <RelVolBadge volume={volume} avgVolume={enriched?.avg_volume} />
            </div>
          ) : (
            <div className="text-xs text-zinc-700">—</div>
          )}
        </div>

        {/* Mkt Cap */}
        <div className="text-center w-20">
          <div className="text-[10px] text-zinc-600 mb-0.5 font-mono uppercase">Mkt Cap</div>
          {marketCap != null ? (
            <div className="text-xs font-mono tabular-nums text-zinc-400">
              ${formatMarketCap(marketCap)}
            </div>
          ) : (
            <div className="text-xs text-zinc-700">—</div>
          )}
        </div>
      </div>

      {/* Price + 52W bar */}
      <div className="text-right shrink-0 w-20">
        {displayPrice != null ? (
          <>
            <div className={`font-mono tabular-nums text-sm text-white font-medium ${flashClass}`}>
              ${displayPrice.toFixed(2)}
            </div>
            <FiftyTwoWeekBar
              price={displayPrice}
              low={enriched?.fifty_two_week_low}
              high={enriched?.fifty_two_week_high}
            />
          </>
        ) : (
          <div className="text-sm text-zinc-600">—</div>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-1 shrink-0">
        <button
          onClick={() => setAlertOpen(true)}
          className="p-1.5 rounded text-zinc-600 hover:text-amber-400 hover:bg-zinc-700 transition-colors"
          title={`Set price alert for ${item.symbol}`}
        >
          <Bell size={13} />
        </button>
        <Link
          href={`/stocks/${item.symbol}`}
          className="p-1.5 rounded text-zinc-500 hover:text-zinc-200 hover:bg-zinc-700 transition-colors text-xs"
          title="View detail"
        >
          →
        </Link>
        <button
          onClick={() => removeMutation.mutate()}
          disabled={removeMutation.isPending}
          className="p-1.5 rounded text-zinc-600 hover:text-red-400 hover:bg-zinc-700 transition-colors text-xs"
          title="Remove from list"
        >
          ✕
        </button>
      </div>

      <AlertDialog
        open={alertOpen}
        onOpenChange={setAlertOpen}
        symbol={item.symbol}
        currentPrice={displayPrice}
      />
    </div>
  )
}
