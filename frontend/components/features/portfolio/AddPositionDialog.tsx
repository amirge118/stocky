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
import { Label } from "@/components/ui/label"
import { searchStocks } from "@/lib/api/stocks"
import { addHolding } from "@/lib/api/portfolio"
import { useToast } from "@/hooks/use-toast"
import type {
  PortfolioPosition,
  PortfolioSummaryWithSector,
} from "@/types/portfolio"
import type { StockSearchResult } from "@/types/stock"

// ── Inline SVG sparkline (copied from AddStockDialog) ───────────────────────
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
  const fillPath = `M ${pts[0]} L ${pts.join(" L ")} L ${W},${H} L 0,${H} Z`
  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} className="shrink-0" aria-hidden>
      <path d={fillPath} fill={fill} />
      <polyline
        points={pts.join(" ")}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

// ── Types ────────────────────────────────────────────────────────────────────
export interface AddPositionDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess?: () => void
}

// ── Main component ───────────────────────────────────────────────────────────
export function AddPositionDialog({ open, onOpenChange, onSuccess }: AddPositionDialogProps) {
  const { toast } = useToast()
  const queryClient = useQueryClient()
  const [step, setStep] = useState<1 | 2>(1)
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<StockSearchResult[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [selected, setSelected] = useState<StockSearchResult | null>(null)
  const [shares, setShares] = useState("")
  const [purchasePrice, setPurchasePrice] = useState("")
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Reset when closed
  useEffect(() => {
    if (!open) {
      setStep(1)
      setQuery("")
      setResults([])
      setIsSearching(false)
      setSelected(null)
      setShares("")
      setPurchasePrice("")
    }
  }, [open])

  // Debounced search
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
    mutationFn: addHolding,
    onMutate: async (variables) => {
      await queryClient.cancelQueries({ queryKey: ["portfolio-summary"] })
      const previous = queryClient.getQueryData<PortfolioSummaryWithSector>(["portfolio-summary"])
      const optimisticPosition: PortfolioPosition = {
        symbol: variables.symbol,
        name: variables.name,
        shares: variables.shares,
        avg_cost: variables.price_per_share,
        total_cost: variables.shares * variables.price_per_share,
        current_price: null,
        current_value: null,
        gain_loss: null,
        gain_loss_pct: null,
        portfolio_pct: null,
        day_change: null,
        day_change_percent: null,
      }
      queryClient.setQueryData<PortfolioSummaryWithSector>(["portfolio-summary"], (old) => {
        if (!old) return old
        const p = old.portfolio
        const newPositions = [...p.positions, optimisticPosition]
        const newTotalCost = p.total_cost + optimisticPosition.total_cost
        return {
          ...old,
          portfolio: {
            ...p,
            positions: newPositions,
            total_cost: newTotalCost,
          },
        }
      })
      return { previous }
    },
    onError: (err: Error, _, context) => {
      if (context?.previous) {
        queryClient.setQueryData(["portfolio-summary"], context.previous)
      }
      toast({ title: "Error", description: err.message, variant: "destructive" })
    },
    onSuccess: () => {
      toast({ title: `${selected?.symbol} added to portfolio` })
      onSuccess?.()
      onOpenChange(false)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["portfolio-summary"] })
      queryClient.invalidateQueries({ queryKey: ["portfolio-history"] })
      queryClient.invalidateQueries({ queryKey: ["portfolio-news"] })
    },
  })

  function handleSelect(result: StockSearchResult) {
    setSelected(result)
    setPurchasePrice(result.current_price != null ? result.current_price.toFixed(2) : "")
    setStep(2)
  }

  function handleSubmit() {
    if (!selected) return
    const sharesNum = parseFloat(shares)
    const priceNum = parseFloat(purchasePrice)
    if (!sharesNum || sharesNum <= 0 || !priceNum || priceNum <= 0) return
    mutation.mutate({
      symbol: selected.symbol,
      name: selected.name,
      shares: sharesNum,
      price_per_share: priceNum,
    })
  }

  const showSkeleton = isSearching
  const showEmpty = !isSearching && query.trim().length > 0 && results.length === 0

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[620px] bg-zinc-900 border-zinc-700">
        <DialogHeader>
          <DialogTitle className="text-white">
            {step === 1 ? "Add Position — Search" : "Add Position — Configure"}
          </DialogTitle>
        </DialogHeader>

        {/* ── Step 1: Search ─────────────────────────────────────────────── */}
        {step === 1 && (
          <>
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
                        </div>

                        {result.sparkline && result.sparkline.length >= 2 ? (
                          <Sparkline data={result.sparkline} />
                        ) : (
                          <div className="w-[72px] shrink-0" />
                        )}

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
                          </div>
                          <Button
                            size="sm"
                            onClick={() => handleSelect(result)}
                            className="bg-zinc-700 hover:bg-zinc-600 text-white border-0"
                          >
                            Select
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
          </>
        )}

        {/* ── Step 2: Configure ──────────────────────────────────────────── */}
        {step === 2 && selected && (
          <div className="space-y-5">
            {/* Selected stock info */}
            <div className="rounded-lg bg-zinc-800 px-4 py-3 flex items-center gap-3">
              <Badge variant="outline" className="font-mono border-zinc-600 text-zinc-200 shrink-0">
                {selected.symbol}
              </Badge>
              <span className="text-white font-medium truncate">{selected.name}</span>
              {selected.current_price != null && (
                <span className="ml-auto text-green-400 font-mono tabular-nums shrink-0">
                  ${selected.current_price.toFixed(2)}
                </span>
              )}
            </div>

            {/* Shares input */}
            <div className="space-y-1.5">
              <Label className="text-zinc-300">Number of shares</Label>
              <Input
                type="number"
                min="0.001"
                step="any"
                placeholder="e.g. 10"
                value={shares}
                onChange={(e) => setShares(e.target.value)}
                className="bg-zinc-800 border-zinc-600 text-white placeholder:text-zinc-500 focus-visible:ring-zinc-500"
              />
            </div>

            {/* Purchase price input */}
            <div className="space-y-1.5">
              <Label className="text-zinc-300">Purchase price per share ($)</Label>
              <Input
                type="number"
                min="0.01"
                step="any"
                placeholder="e.g. 150.00"
                value={purchasePrice}
                onChange={(e) => setPurchasePrice(e.target.value)}
                className="bg-zinc-800 border-zinc-600 text-white placeholder:text-zinc-500 focus-visible:ring-zinc-500"
              />
            </div>

            <div className="flex justify-between pt-1">
              <Button
                variant="ghost"
                onClick={() => setStep(1)}
                className="text-zinc-400 hover:text-white hover:bg-zinc-800"
              >
                ← Back
              </Button>
              <Button
                onClick={handleSubmit}
                disabled={
                  mutation.isPending ||
                  !shares ||
                  parseFloat(shares) <= 0 ||
                  !purchasePrice ||
                  parseFloat(purchasePrice) <= 0
                }
                className="bg-blue-600 hover:bg-blue-500 text-white"
              >
                {mutation.isPending ? "Adding…" : "Add to Portfolio"}
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
