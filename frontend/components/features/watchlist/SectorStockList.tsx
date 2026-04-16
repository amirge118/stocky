"use client"

import { BarChart2, CheckCircle2, TrendingDown, TrendingUp } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import type { SectorPeer } from "@/lib/api/stocks"

interface SectorStockListProps {
  stocks: SectorPeer[]
  existingSymbols: Set<string>
  selected: Set<string>
  onToggleSelect: (symbol: string) => void
  onAddSingle: (peer: SectorPeer) => void
  addingSymbol: string | null
  rowErrors: Record<string, string>
  loading: boolean
}

export function SectorStockList({
  stocks,
  existingSymbols,
  selected,
  onToggleSelect,
  onAddSingle,
  addingSymbol,
  rowErrors,
  loading,
}: SectorStockListProps) {
  if (loading) {
    return (
      <div className="space-y-1.5 mt-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-[52px] rounded-lg bg-zinc-800/60 animate-pulse" />
        ))}
      </div>
    )
  }

  if (stocks.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-10 text-zinc-500">
        <BarChart2 className="w-8 h-8 mb-2 opacity-40" />
        <p className="text-sm">No stocks found in this sector.</p>
      </div>
    )
  }

  return (
    <ul className="mt-2 space-y-1">
      {stocks.map((peer) => {
        const already = existingSymbols.has(peer.symbol)
        const checked = selected.has(peer.symbol)
        const isAdding = addingSymbol === peer.symbol
        const isUp = (peer.day_change_percent ?? 0) >= 0
        const hasError = !!rowErrors[peer.symbol]

        return (
          <li
            key={peer.symbol}
            className={[
              "group flex items-center gap-3 px-3 py-2.5 rounded-lg border transition-all duration-150",
              already
                ? "bg-zinc-800/30 border-zinc-700/50 opacity-60"
                : hasError
                  ? "bg-red-900/10 border-red-800/50"
                  : checked
                    ? "bg-zinc-800 border-zinc-600"
                    : "bg-zinc-800/50 border-zinc-700/50 hover:bg-zinc-800 hover:border-zinc-600",
            ].join(" ")}
          >
            <Checkbox
              checked={checked || already}
              disabled={already}
              onCheckedChange={() => !already && onToggleSelect(peer.symbol)}
              className="shrink-0"
              aria-label={`Select ${peer.symbol}`}
            />

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5">
                <Badge
                  variant="outline"
                  className="font-mono text-[10px] px-1.5 py-0 h-[18px] border-zinc-600 text-zinc-300 bg-zinc-800/80 shrink-0"
                >
                  {peer.symbol}
                </Badge>
                <span className="font-medium text-sm text-zinc-100 truncate">{peer.name}</span>
                {already && (
                  <CheckCircle2 className="w-3.5 h-3.5 text-green-400 shrink-0 ml-auto" />
                )}
              </div>
              {peer.industry && (
                <p className="text-[11px] text-zinc-500 mt-0.5 truncate">{peer.industry}</p>
              )}
              {hasError && (
                <p className="text-[11px] text-red-400 mt-0.5">{rowErrors[peer.symbol]}</p>
              )}
            </div>

            <div className="flex items-center gap-3 shrink-0">
              <div className="text-right w-[72px]">
                <div className="text-sm font-mono tabular-nums text-zinc-200">
                  {peer.current_price != null
                    ? peer.current_price.toLocaleString("en-US", {
                        style: "currency",
                        currency: "USD",
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })
                    : "—"}
                </div>
                <div
                  className={`flex items-center justify-end gap-0.5 text-[11px] tabular-nums ${
                    isUp ? "text-green-400" : "text-red-400"
                  }`}
                >
                  {peer.day_change_percent != null ? (
                    <>
                      {isUp ? (
                        <TrendingUp className="w-3 h-3" />
                      ) : (
                        <TrendingDown className="w-3 h-3" />
                      )}
                      {isUp ? "+" : ""}
                      {peer.day_change_percent.toFixed(2)}%
                    </>
                  ) : (
                    "—"
                  )}
                </div>
              </div>

              <Button
                size="sm"
                disabled={already || isAdding}
                onClick={() => !already && onAddSingle(peer)}
                className={[
                  "w-16 h-8 text-xs font-medium border transition-all",
                  already
                    ? "bg-transparent border-zinc-700 text-zinc-500 cursor-default pointer-events-none"
                    : "bg-zinc-700 hover:bg-zinc-600 border-zinc-600 text-zinc-100 hover:text-white hover:border-zinc-500",
                ].join(" ")}
              >
                {already ? "Added" : isAdding ? "…" : "Add"}
              </Button>
            </div>
          </li>
        )
      })}
    </ul>
  )
}
