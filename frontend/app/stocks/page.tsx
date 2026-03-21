"use client"

import { useState, useCallback, useEffect, Suspense } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { Plus, Bell } from "lucide-react"
import { Button } from "@/components/ui/button"
import { getStocks } from "@/lib/api/stocks"
import { StockSearchFilter } from "@/components/features/stocks/StockSearchFilter"
import { StockTable } from "@/components/features/stocks/StockTable"
import { BulkActionsBar } from "@/components/features/stocks/BulkActionsBar"
import { BulkDeleteDialog } from "@/components/features/stocks/BulkDeleteDialog"
import { AddStockDialog } from "@/components/features/stocks/AddStockDialog"
import { WatchlistPanel } from "@/components/features/stocks/WatchlistPanel"
import { AlertDialog } from "@/components/features/stocks/AlertDialog"
import { useWatchlist } from "@/lib/hooks/useWatchlist"
import type { Stock } from "@/types/stock"

function StocksContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const { addToWatchlist, removeFromWatchlist } = useWatchlist()
  const [dialogOpen, setDialogOpen] = useState(false)
  const [bulkDeleteOpen, setBulkDeleteOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState(() => searchParams.get("q") ?? "")
  const [exchangeFilter, setExchangeFilter] = useState<string | undefined>(
    () => searchParams.get("exchange") ?? undefined
  )
  const [sectorFilter, setSectorFilter] = useState<string | undefined>(
    () => searchParams.get("sector") ?? undefined
  )
  const [watchlistOnly, setWatchlistOnly] = useState(
    () => searchParams.get("watchlist") === "true"
  )
  const [selectedStocks, setSelectedStocks] = useState<Stock[]>([])
  const [alertDialogOpen, setAlertDialogOpen] = useState(false)
  const queryClient = useQueryClient()

  useEffect(() => {
    setSearchQuery(searchParams.get("q") ?? "")
    setExchangeFilter(searchParams.get("exchange") ?? undefined)
    setSectorFilter(searchParams.get("sector") ?? undefined)
    setWatchlistOnly(searchParams.get("watchlist") === "true")
  }, [searchParams])

  const updateUrl = useCallback(
    (
      newSearch: string,
      newExchange: string | undefined,
      newSector: string | undefined,
      newWatchlist: boolean
    ) => {
      const params = new URLSearchParams()
      if (newSearch) params.set("q", newSearch)
      if (newExchange) params.set("exchange", newExchange)
      if (newSector) params.set("sector", newSector)
      if (newWatchlist) params.set("watchlist", "true")
      const qs = params.toString()
      router.replace(`/stocks${qs ? `?${qs}` : ""}`)
    },
    [router]
  )

  const handleSearchChange = useCallback(
    (value: string) => {
      setSearchQuery(value)
      updateUrl(value, exchangeFilter, sectorFilter, watchlistOnly)
    },
    [exchangeFilter, sectorFilter, watchlistOnly, updateUrl]
  )

  const handleExchangeFilterChange = useCallback(
    (value: string | undefined) => {
      setExchangeFilter(value)
      updateUrl(searchQuery, value, sectorFilter, watchlistOnly)
    },
    [searchQuery, sectorFilter, watchlistOnly, updateUrl]
  )

  const handleSectorFilterChange = useCallback(
    (value: string | undefined) => {
      setSectorFilter(value)
      updateUrl(searchQuery, exchangeFilter, value, watchlistOnly)
    },
    [searchQuery, exchangeFilter, watchlistOnly, updateUrl]
  )

  const handleWatchlistOnlyChange = useCallback(
    (value: boolean) => {
      setWatchlistOnly(value)
      updateUrl(searchQuery, exchangeFilter, sectorFilter, value)
    },
    [searchQuery, exchangeFilter, sectorFilter, updateUrl]
  )

  const { data, isPending, isError, error } = useQuery({
    queryKey: ["stocks", 1, 500],
    queryFn: () => getStocks({ page: 1, limit: 500 }),
  })

  const stocks = data?.data ?? []

  const handleBulkDelete = useCallback((toDelete: Stock[]) => {
    setSelectedStocks(toDelete)
    setBulkDeleteOpen(true)
  }, [])

  const handleBulkAddToWatchlist = useCallback(
    (stocksToAdd: Stock[]) => {
      stocksToAdd.forEach((s) => addToWatchlist(s.symbol))
    },
    [addToWatchlist]
  )

  const handleBulkRemoveFromWatchlist = useCallback(
    (stocksToRemove: Stock[]) => {
      stocksToRemove.forEach((s) => removeFromWatchlist(s.symbol))
    },
    [removeFromWatchlist]
  )

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Main content */}
          <div className="flex-1 min-w-0 space-y-5">
            {/* Header */}
            <div className="flex items-end justify-between gap-4">
              <div>
                <p className="text-[11px] font-medium tracking-widest uppercase text-zinc-500 mb-1">
                  Stock Browser
                </p>
                <h1 className="text-3xl font-bold tracking-tight text-white leading-none">
                  Stocks
                </h1>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={() => setAlertDialogOpen(true)}
                  className="h-8 px-3 text-xs border-zinc-600 text-zinc-300 hover:bg-zinc-800"
                >
                  <Bell size={13} className="mr-1" />
                  Alerts
                </Button>
                <Button
                  onClick={() => setDialogOpen(true)}
                  className="h-8 px-3 text-xs font-semibold bg-white text-zinc-950 hover:bg-zinc-100 rounded-lg gap-1.5"
                >
                  <Plus size={13} />
                  Add Stock
                </Button>
              </div>
            </div>

            {/* Search & Filters */}
            <StockSearchFilter
              stocks={stocks}
              searchQuery={searchQuery}
              onSearchChange={handleSearchChange}
              exchangeFilter={exchangeFilter}
              onExchangeFilterChange={handleExchangeFilterChange}
              sectorFilter={sectorFilter}
              onSectorFilterChange={handleSectorFilterChange}
              watchlistOnly={watchlistOnly}
              onWatchlistOnlyChange={handleWatchlistOnlyChange}
            />

            {/* Bulk Actions */}
            <BulkActionsBar
              selectedStocks={selectedStocks}
              allStocks={stocks}
              onSelectAll={() => setSelectedStocks([...stocks])}
              onDeselectAll={() => setSelectedStocks([])}
              onBulkDelete={handleBulkDelete}
              onBulkAddToWatchlist={handleBulkAddToWatchlist}
              onBulkRemoveFromWatchlist={handleBulkRemoveFromWatchlist}
            />

            {/* Stock Table */}
            {isError ? (
              <div
                role="alert"
                className="rounded-lg border border-destructive bg-destructive/10 p-4 text-sm text-destructive"
              >
                {error instanceof Error ? error.message : "Failed to load stocks. Please try again."}
              </div>
            ) : isPending ? (
              <div className="rounded-xl border border-zinc-800 bg-zinc-900 overflow-hidden">
                <div className="divide-y divide-zinc-800">
                  {Array.from({ length: 8 }).map((_, i) => (
                    <div key={i} className="flex items-center gap-4 px-4 py-3 animate-pulse">
                      <div className="h-4 w-16 rounded bg-zinc-800" />
                      <div className="h-4 w-32 rounded bg-zinc-800 flex-1" />
                      <div className="h-4 w-20 rounded bg-zinc-800" />
                      <div className="h-4 w-16 rounded bg-zinc-800" />
                      <div className="h-6 w-24 rounded bg-zinc-800" />
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <StockTable
                stocks={stocks}
                searchQuery={searchQuery}
                filters={{
                  exchange: exchangeFilter,
                  sector: sectorFilter,
                  watchlistOnly,
                }}
                selectedStocks={selectedStocks}
                onSelectionChange={setSelectedStocks}
                onBulkDelete={handleBulkDelete}
                onEdit={() => queryClient.invalidateQueries({ queryKey: ["stocks"] })}
                onDelete={() => queryClient.invalidateQueries({ queryKey: ["stocks"] })}
              />
            )}
          </div>

          {/* Watchlist Sidebar */}
          <aside className="lg:w-72 shrink-0">
            <div className="lg:sticky lg:top-20">
              <WatchlistPanel />
            </div>
          </aside>
        </div>

        {/* Dialogs */}
        <AddStockDialog
          open={dialogOpen}
          onOpenChange={setDialogOpen}
          onSuccess={() => queryClient.invalidateQueries({ queryKey: ["stocks"] })}
        />
        <BulkDeleteDialog
          open={bulkDeleteOpen}
          onOpenChange={setBulkDeleteOpen}
          stocks={selectedStocks}
          onSuccess={() => {
            queryClient.invalidateQueries({ queryKey: ["stocks"] })
            setSelectedStocks([])
          }}
        />
        <AlertDialog open={alertDialogOpen} onOpenChange={setAlertDialogOpen} />
      </div>
    </div>
  )
}

export default function StocksPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
          <div className="animate-pulse h-8 w-48 rounded bg-zinc-800" />
        </div>
      }
    >
      <StocksContent />
    </Suspense>
  )
}
