"use client"

import { useRouter } from "next/navigation"
import { Star, Trash2, ChevronRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useWatchlist } from "@/lib/hooks/useWatchlist"

export function WatchlistPanel() {
  const router = useRouter()
  const { watchlist, removeFromWatchlist, clearWatchlist } = useWatchlist()

  if (watchlist.length === 0) {
    return (
      <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6">
        <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wide mb-3 flex items-center gap-2">
          <Star size={14} className="text-amber-400" />
          Watchlist
        </h3>
        <p className="text-zinc-500 text-sm">
          No symbols in watchlist. Add stocks from the table to track them.
        </p>
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wide flex items-center gap-2">
          <Star size={14} className="text-amber-400" />
          Watchlist ({watchlist.length})
        </h3>
        <Button
          variant="ghost"
          size="sm"
          className="h-7 text-xs text-zinc-500 hover:text-zinc-300"
          onClick={clearWatchlist}
        >
          Clear all
        </Button>
      </div>
      <ul className="space-y-1">
        {watchlist.map((symbol) => (
          <li
            key={symbol}
            className="flex items-center justify-between group py-1.5 px-2 rounded-lg hover:bg-zinc-800/50 transition-colors"
          >
            <button
              type="button"
              onClick={() => router.push(`/stocks/${symbol}`)}
              className="flex items-center gap-2 flex-1 min-w-0 text-left"
            >
              <span className="font-mono font-medium text-white text-sm truncate">
                {symbol}
              </span>
              <ChevronRight size={14} className="text-zinc-500 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />
            </button>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7 shrink-0 text-zinc-500 hover:text-red-400"
              onClick={() => removeFromWatchlist(symbol)}
              aria-label={`Remove ${symbol} from watchlist`}
            >
              <Trash2 size={14} />
            </Button>
          </li>
        ))}
      </ul>
    </div>
  )
}
