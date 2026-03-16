"use client"

import Link from "next/link"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { removeItemFromWatchlist } from "@/lib/api/watchlists"
import { Sparkline } from "@/components/features/stocks/Sparkline"
import type { WatchlistItem, WatchlistListResponse, WatchlistListSummary } from "@/types/watchlist"
import type { PriceUpdate } from "@/lib/hooks/useStockPrices"

interface WatchlistStockRowProps {
  item: WatchlistItem
  listId: number
  price: PriceUpdate | undefined
  sparkline: number[] | undefined
}

export function WatchlistStockRow({
  item,
  listId,
  price,
  sparkline,
}: WatchlistStockRowProps) {
  const queryClient = useQueryClient()

  const removeMutation = useMutation({
    mutationFn: () => removeItemFromWatchlist(listId, item.symbol),
    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey: ["watchlists", listId] })
      const prev = queryClient.getQueryData<WatchlistListResponse>(["watchlists", listId])
      queryClient.setQueryData<WatchlistListResponse>(["watchlists", listId], (old) =>
        old ? { ...old, items: old.items.filter((i) => i.id !== item.id) } : old
      )
      // Decrement sidebar count
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
  const changePct = price?.change_percent
  const isUp = changePct !== undefined ? changePct >= 0 : true

  return (
    <div className="flex items-center gap-4 px-4 py-3 rounded-lg bg-zinc-900/50 hover:bg-zinc-800/60 transition-colors">
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
        </div>
        {item.sector && (
          <span className="text-xs text-zinc-600 mt-0.5 block">{item.sector}</span>
        )}
      </div>

      {/* Sparkline */}
      <div className="shrink-0">
        {sparkline && sparkline.length >= 2 ? (
          <Sparkline data={sparkline} width={80} height={28} />
        ) : (
          <div className="w-20 h-7 bg-zinc-800/50 rounded animate-pulse" />
        )}
      </div>

      {/* Price + change */}
      <div className="text-right shrink-0 w-28">
        {displayPrice != null ? (
          <>
            <div className="font-mono tabular-nums text-sm text-white font-medium">
              ${displayPrice.toFixed(2)}
            </div>
            {changePct != null && (
              <div className={`text-xs font-mono tabular-nums ${isUp ? "text-green-400" : "text-red-400"}`}>
                {isUp ? "+" : ""}{changePct.toFixed(2)}%
              </div>
            )}
          </>
        ) : (
          <div className="text-sm text-zinc-600">—</div>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-1 shrink-0">
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
    </div>
  )
}
