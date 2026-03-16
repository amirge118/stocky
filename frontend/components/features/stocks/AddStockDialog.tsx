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
import { createStock, searchStocks } from "@/lib/api/stocks"
import { useToast } from "@/hooks/use-toast"
import type { Stock, StockListResponse, StockSearchResult } from "@/types/stock"

// ── Inline SVG sparkline ────────────────────────────────────────────────────
function Sparkline({ data }: { data: number[] }) {
  if (data.length < 2) return null

  const W = 72
  const H = 28
  const min = Math.min(...data)
  const max = Math.max(...data)
  const range = max - min || 1
  const isUp = data[data.length - 1] >= data[0]
  const color = isUp ? "#16a34a" : "#dc2626"
  const fill = isUp ? "#16a34a22" : "#dc262622"

  const pts = data.map((v, i) => {
    const x = (i / (data.length - 1)) * W
    const y = H - ((v - min) / range) * (H - 4) - 2
    return `${x.toFixed(1)},${y.toFixed(1)}`
  })

  const polyPoints = pts.join(" ")
  // Closed path for fill: line + bottom-right + bottom-left
  const fillPath = `M ${pts[0]} L ${pts.join(" L ")} L ${W},${H} L 0,${H} Z`

  return (
    <svg
      width={W}
      height={H}
      viewBox={`0 0 ${W} ${H}`}
      className="shrink-0"
      aria-hidden
    >
      <path d={fillPath} fill={fill} />
      <polyline
        points={polyPoints}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

// ── Main dialog ─────────────────────────────────────────────────────────────
export interface AddStockDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess?: () => void
}

export function AddStockDialog({
  open,
  onOpenChange,
  onSuccess,
}: AddStockDialogProps) {
  const { toast } = useToast()
  const queryClient = useQueryClient()
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<StockSearchResult[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [rowErrors, setRowErrors] = useState<Record<string, string>>({})
  const [addingSymbol, setAddingSymbol] = useState<string | null>(null)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (!open) {
      setQuery("")
      setResults([])
      setIsSearching(false)
      setRowErrors({})
      setAddingSymbol(null)
    }
  }, [open])

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)

    if (query.trim().length < 1) {
      setResults([])
      setIsSearching(false)
      return
    }

    setIsSearching(true)
    debounceRef.current = setTimeout(async () => {
      try {
        const data = await searchStocks(query.trim())
        setResults(data)
      } catch {
        setResults([])
      } finally {
        setIsSearching(false)
      }
    }, 400)

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [query])

  const mutation = useMutation({
    mutationFn: createStock,
    onMutate: async (variables) => {
      await queryClient.cancelQueries({ queryKey: ["stocks"] })
      const previous = queryClient.getQueriesData({ queryKey: ["stocks"] })
      const optimisticStock: Stock = {
        id: Date.now(),
        symbol: variables.symbol,
        name: variables.name,
        exchange: variables.exchange,
        sector: variables.sector ?? null,
        created_at: new Date().toISOString(),
        updated_at: null,
      }
      queryClient.setQueriesData<StockListResponse>(
        { predicate: (q) => q.queryKey[0] === "stocks" },
        (old) => {
          if (!old) return old
          const newData = [...old.data, optimisticStock]
          return {
            ...old,
            data: newData,
            meta: {
              ...old.meta,
              total: old.meta.total + 1,
            },
          }
        }
      )
      return { previous }
    },
    onError: (error: Error, variables, context) => {
      if (context?.previous) {
        for (const [queryKey, data] of context.previous) {
          queryClient.setQueryData(queryKey, data)
        }
      }
      setRowErrors((prev) => ({
        ...prev,
        [variables.symbol]: error.message || "Failed to add stock",
      }))
      setAddingSymbol(null)
      // If stock already exists, refetch list so user sees it in the table
      if (error.message?.toLowerCase().includes("already exists")) {
        queryClient.refetchQueries({ queryKey: ["stocks"] })
        toast({
          title: "Stock already in list",
          description: `${variables.symbol} is already in your stocks. Refreshing the list.`,
        })
      }
    },
    onSuccess: (_, variables) => {
      toast({ title: `${variables.symbol} added` })
      setAddingSymbol(null)
      onSuccess?.()
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["stocks"] })
    },
  })

  const handleAdd = (result: StockSearchResult) => {
    setRowErrors((prev) => {
      const next = { ...prev }
      delete next[result.symbol]
      return next
    })
    setAddingSymbol(result.symbol)
    mutation.mutate({
      symbol: result.symbol,
      name: result.name,
      exchange: result.exchange,
      sector: result.sector ?? null,
    })
  }

  const showSkeleton = isSearching
  const showEmpty = !isSearching && query.trim().length > 0 && results.length === 0

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[620px] bg-zinc-900 border-zinc-700">
        <DialogHeader>
          <DialogTitle className="text-white">Add Stock</DialogTitle>
        </DialogHeader>

        {/* Search input */}
        <div className="relative">
          <Input
            autoFocus
            aria-label="Symbol"
            placeholder="Search by ticker or company name..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="pr-10 bg-zinc-800 border-zinc-600 text-white placeholder:text-zinc-400 focus-visible:ring-zinc-500"
          />
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 pointer-events-none text-sm">
            🔍
          </span>
        </div>

        {/* Results */}
        <div className="min-h-[120px]">
          {showSkeleton && (
            <div className="space-y-2 mt-2">
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  className="h-16 rounded-md bg-zinc-800 animate-pulse"
                />
              ))}
            </div>
          )}

          {showEmpty && (
            <p className="text-sm text-zinc-400 text-center py-8">
              No results found for &ldquo;{query}&rdquo;
            </p>
          )}

          {!isSearching && results.length > 0 && (
            <ul className="divide-y divide-zinc-700 mt-2 rounded-md border border-zinc-700 overflow-hidden">
              {results.map((result) => {
                const priceChange =
                  result.sparkline && result.sparkline.length >= 2
                    ? result.sparkline[result.sparkline.length - 1] - result.sparkline[0]
                    : null
                const isUp = priceChange !== null ? priceChange >= 0 : true

                return (
                  <li
                    key={result.symbol}
                    className="flex items-center gap-4 px-4 py-3 bg-zinc-900 hover:bg-zinc-800 transition-colors"
                  >
                    {/* Left: symbol + name + sector */}
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
                        <p className="text-xs text-red-400 mt-0.5">
                          {rowErrors[result.symbol]}
                        </p>
                      )}
                    </div>

                    {/* Center: sparkline */}
                    {result.sparkline && result.sparkline.length >= 2 ? (
                      <Sparkline data={result.sparkline} />
                    ) : (
                      <div className="w-[72px] shrink-0" />
                    )}

                    {/* Right: price + add button */}
                    <div className="flex items-center gap-3 shrink-0">
                      <div className="text-right">
                        {result.current_price != null ? (
                          <span
                            className={`text-sm font-mono tabular-nums font-semibold ${
                              isUp ? "text-green-400" : "text-red-400"
                            }`}
                          >
                            ${result.current_price.toFixed(2)}
                          </span>
                        ) : (
                          <span className="text-sm text-zinc-500">—</span>
                        )}
                        {result.currency && result.currency !== "USD" && (
                          <span className="block text-xs text-zinc-500">
                            {result.currency}
                          </span>
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
