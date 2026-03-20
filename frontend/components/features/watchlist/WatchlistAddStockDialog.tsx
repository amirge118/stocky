"use client"

import { useState, useEffect, useRef } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { searchStocks } from "@/lib/api/stocks"
import { addItemToWatchlist } from "@/lib/api/watchlists"
import { useToast } from "@/hooks/use-toast"
import { Sparkline } from "@/components/features/stocks/Sparkline"
import type { StockSearchResult } from "@/types/stock"
import type { WatchlistItem, WatchlistListResponse } from "@/types/watchlist"

interface WatchlistAddStockDialogProps {
  open: boolean
  listId: number
  listName: string
  onOpenChange: (open: boolean) => void
}

export function WatchlistAddStockDialog({
  open,
  listId,
  listName,
  onOpenChange,
}: WatchlistAddStockDialogProps) {
  const { toast } = useToast()
  const queryClient = useQueryClient()
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<StockSearchResult[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [searchError, setSearchError] = useState<string | null>(null)
  const [rowErrors, setRowErrors] = useState<Record<string, string>>({})
  const [addingSymbol, setAddingSymbol] = useState<string | null>(null)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (!open) {
      setQuery("")
      setResults([])
      setIsSearching(false)
      setSearchError(null)
      setRowErrors({})
      setAddingSymbol(null)
    }
  }, [open])

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    if (query.trim().length < 1) { setResults([]); setIsSearching(false); return }
    setIsSearching(true)
    setSearchError(null)
    debounceRef.current = setTimeout(async () => {
      try {
        const data = await searchStocks(query.trim())
        setResults(data)
      } catch (err) {
        setResults([])
        setSearchError(err instanceof Error ? err.message : "Search failed")
      } finally {
        setIsSearching(false)
      }
    }, 400)
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current) }
  }, [query])

  const mutation = useMutation({
    mutationFn: (result: StockSearchResult) =>
      addItemToWatchlist(listId, {
        symbol: result.symbol,
        name: result.name,
        exchange: result.exchange,
        sector: result.sector ?? null,
      }),
    onMutate: async (result) => {
      await queryClient.cancelQueries({ queryKey: ["watchlists", listId] })
      const prev = queryClient.getQueryData<WatchlistListResponse>(["watchlists", listId])
      const optimistic: WatchlistItem = {
        id: -Date.now(),
        watchlist_id: listId,
        symbol: result.symbol,
        name: result.name,
        exchange: result.exchange,
        sector: result.sector ?? null,
        position: 0,
        created_at: new Date().toISOString(),
      }
      queryClient.setQueryData<WatchlistListResponse>(["watchlists", listId], (old) =>
        old ? { ...old, items: [...old.items, optimistic] } : old
      )
      // Increment sidebar count
      queryClient.setQueryData<import("@/types/watchlist").WatchlistListSummary[]>(
        ["watchlists"],
        (old) =>
          old?.map((l) =>
            l.id === listId ? { ...l, item_count: l.item_count + 1 } : l
          )
      )
      return { prev }
    },
    onError: (error: Error, result, ctx) => {
      if (ctx?.prev) queryClient.setQueryData(["watchlists", listId], ctx.prev)
      queryClient.invalidateQueries({ queryKey: ["watchlists"] })
      setRowErrors((prev) => ({ ...prev, [result.symbol]: error.message || "Failed to add" }))
      setAddingSymbol(null)
    },
    onSuccess: (_item, result) => {
      toast({ title: `${result.symbol} added to ${listName}` })
      setAddingSymbol(null)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["watchlists", listId] })
      queryClient.invalidateQueries({ queryKey: ["watchlists"] })
    },
  })

  const handleAdd = (result: StockSearchResult) => {
    setRowErrors((prev) => { const next = { ...prev }; delete next[result.symbol]; return next })
    setAddingSymbol(result.symbol)
    mutation.mutate(result)
  }

  const showSkeleton = isSearching
  const showEmpty = !isSearching && !searchError && query.trim().length > 0 && results.length === 0

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[620px] bg-zinc-900 border-zinc-700">
        <DialogHeader>
          <DialogTitle className="text-white">Add to {listName}</DialogTitle>
        </DialogHeader>

        <div className="relative">
          <Input
            autoFocus
            placeholder="Search by ticker or company name..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="pr-10 bg-zinc-800 border-zinc-600 text-white placeholder:text-zinc-400 focus-visible:ring-zinc-500"
          />
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 pointer-events-none text-sm">
            🔍
          </span>
        </div>

        <div className="min-h-[120px]">
          {showSkeleton && (
            <div className="space-y-2 mt-2">
              {[0, 1, 2].map((i) => (
                <div key={i} className="h-16 rounded-md bg-zinc-800 animate-pulse" />
              ))}
            </div>
          )}

          {searchError && (
            <p className="text-sm text-amber-400 text-center py-8">{searchError}</p>
          )}

          {showEmpty && (
            <p className="text-sm text-zinc-400 text-center py-8">
              No results found for &ldquo;{query}&rdquo;
            </p>
          )}

          {!isSearching && results.length > 0 && (
            <ul className="divide-y divide-zinc-700 mt-2 rounded-md border border-zinc-700 overflow-hidden">
              {results.map((result) => {
                const isUp =
                  result.sparkline && result.sparkline.length >= 2
                    ? result.sparkline[result.sparkline.length - 1] >= result.sparkline[0]
                    : true

                return (
                  <li
                    key={result.symbol}
                    className="flex items-center gap-4 px-4 py-3 bg-zinc-900 hover:bg-zinc-800 transition-colors"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge
                          variant="outline"
                          className="font-mono text-xs shrink-0 border-zinc-600 text-zinc-200"
                        >
                          {result.symbol}
                        </Badge>
                        <span className="font-medium text-sm text-white truncate">
                          {result.name}
                        </span>
                        <span className="text-xs text-zinc-400 shrink-0">
                          {result.exchange}
                        </span>
                      </div>
                      <div className="flex items-center gap-1 mt-0.5 text-xs text-zinc-500">
                        {result.sector && <span>{result.sector}</span>}
                        {result.sector && result.industry && <span>·</span>}
                        {result.industry && <span>{result.industry}</span>}
                      </div>
                      {rowErrors[result.symbol] && (
                        <p className="text-xs text-red-400 mt-0.5">{rowErrors[result.symbol]}</p>
                      )}
                    </div>

                    {result.sparkline && result.sparkline.length >= 2 ? (
                      <Sparkline data={result.sparkline} />
                    ) : (
                      <div className="w-[72px] shrink-0" />
                    )}

                    <div className="flex items-center gap-3 shrink-0">
                      <div className="text-right">
                        {result.current_price != null ? (
                          <span className={`text-sm font-mono tabular-nums font-semibold ${isUp ? "text-green-400" : "text-red-400"}`}>
                            ${result.current_price.toFixed(2)}
                          </span>
                        ) : (
                          <span className="text-sm text-zinc-500">—</span>
                        )}
                      </div>
                      <Button
                        size="sm"
                        onClick={() => handleAdd(result)}
                        disabled={addingSymbol === result.symbol}
                        className="bg-zinc-700 hover:bg-zinc-600 text-white border-0"
                      >
                        {addingSymbol === result.symbol ? "Adding…" : "Add"}
                      </Button>
                    </div>
                  </li>
                )
              })}
            </ul>
          )}
        </div>

        <div className="flex justify-end pt-1">
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            className="border-zinc-600 text-zinc-300 hover:bg-zinc-800 hover:text-white"
          >
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
