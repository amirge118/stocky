"use client"

import { useState, useCallback } from "react"
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

export default function StocksPage() {
  const { addToWatchlist, removeFromWatchlist } = useWatchlist()
  const [dialogOpen, setDialogOpen] = useState(false)
  const [bulkDeleteOpen, setBulkDeleteOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const [exchangeFilter, setExchangeFilter] = useState<string | undefined>()
  const [sectorFilter, setSectorFilter] = useState<string | undefined>()
  const [watchlistOnly, setWatchlistOnly] = useState(false)
  const [selectedStocks, setSelectedStocks] = useState<Stock[]>([])
  const [alertDialogOpen, setAlertDialogOpen] = useState(false)
  const queryClient = useQueryClient()

  const { data, isPending } = useQuery({
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
              onSearchChange={setSearchQuery}
              exchangeFilter={exchangeFilter}
              onExchangeFilterChange={setExchangeFilter}
              sectorFilter={sectorFilter}
              onSectorFilterChange={setSectorFilter}
              watchlistOnly={watchlistOnly}
              onWatchlistOnlyChange={setWatchlistOnly}
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
            {isPending ? (
              <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-12 animate-pulse">
                <div className="h-5 w-32 rounded bg-zinc-700 mb-4" />
                <div className="h-64 rounded bg-zinc-800" />
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
