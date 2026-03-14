"use client"

import { useState, useMemo } from "react"
import { useQuery } from "@tanstack/react-query"
import { useRouter } from "next/navigation"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Edit, Trash2, TrendingUp, TrendingDown, Star, StarOff } from "lucide-react"
import { fetchStockData } from "@/lib/api/stocks"
import { useWatchlist } from "@/lib/hooks/useWatchlist"
import type { Stock, StockData } from "@/types/stock"
import { EditStockDialog } from "./EditStockDialog"
import { DeleteStockDialog } from "./DeleteStockDialog"

export interface StockTableProps {
  stocks: Stock[]
  searchQuery?: string
  filters?: {
    exchange?: string
    sector?: string
    watchlistOnly?: boolean
  }
  onEdit?: (stock: Stock) => void
  onDelete?: (stock: Stock) => void
  onBulkDelete?: (stocks: Stock[]) => void
  selectedStocks?: Stock[]
  onSelectionChange?: (stocks: Stock[]) => void
}

interface StockWithData extends Stock {
  liveData?: StockData
  isLoadingData?: boolean
}

export function StockTable({
  stocks,
  searchQuery = "",
  filters = {},
  onEdit,
  onDelete,
  onBulkDelete: _onBulkDelete,
  selectedStocks = [],
  onSelectionChange,
}: StockTableProps) {
  const router = useRouter()
  const { isInWatchlist, toggleWatchlist } = useWatchlist()
  const [editingStock, setEditingStock] = useState<Stock | null>(null)
  const [deletingStock, setDeletingStock] = useState<Stock | null>(null)

  // Filter stocks based on search and filters
  const filteredStocks = useMemo(() => {
    let filtered = [...stocks]

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(
        (stock) =>
          stock.symbol.toLowerCase().includes(query) ||
          stock.name.toLowerCase().includes(query) ||
          stock.exchange.toLowerCase().includes(query) ||
          (stock.sector && stock.sector.toLowerCase().includes(query))
      )
    }

    // Exchange filter
    if (filters.exchange) {
      filtered = filtered.filter((stock) => stock.exchange === filters.exchange)
    }

    // Sector filter
    if (filters.sector) {
      filtered = filtered.filter((stock) => stock.sector === filters.sector)
    }

    // Watchlist filter
    if (filters.watchlistOnly) {
      filtered = filtered.filter((stock) => isInWatchlist(stock.symbol))
    }

    return filtered
  }, [stocks, searchQuery, filters, isInWatchlist])

  // Fetch live data for all stocks (limit to prevent too many parallel requests)
  const stockDataQueries = useQuery({
    queryKey: [
      "stockData",
      filteredStocks.slice(0, 50).map((s) => s.symbol).sort().join(","),
    ],
    queryFn: async () => {
      const dataMap = new Map<string, StockData>()
      // Limit concurrent requests to prevent overwhelming the API
      const stocksToFetch = filteredStocks.slice(0, 50)
      const promises = stocksToFetch.map(async (stock) => {
        try {
          const data = await fetchStockData(stock.symbol)
          dataMap.set(stock.symbol, data)
        } catch (error) {
          console.error(`Failed to fetch data for ${stock.symbol}:`, error)
          // Don't throw - allow other stocks to load even if one fails
        }
      })
      await Promise.all(promises)
      return dataMap
    },
    enabled: filteredStocks.length > 0 && filteredStocks.length <= 50,
    staleTime: 30 * 1000, // 30 seconds
    refetchOnWindowFocus: true,
  })

  const stocksWithData: StockWithData[] = useMemo(() => {
    const dataMap = stockDataQueries.data || new Map()
    return filteredStocks.map((stock) => ({
      ...stock,
      liveData: dataMap.get(stock.symbol),
      isLoadingData: stockDataQueries.isLoading,
    }))
  }, [filteredStocks, stockDataQueries.data, stockDataQueries.isLoading])

  const handleSelectStock = (stock: Stock, checked: boolean) => {
    if (!onSelectionChange) return

    if (checked) {
      onSelectionChange([...selectedStocks, stock])
    } else {
      onSelectionChange(selectedStocks.filter((s) => s.id !== stock.id))
    }
  }

  const handleSelectAll = (checked: boolean) => {
    if (!onSelectionChange) return

    if (checked) {
      onSelectionChange([...stocksWithData])
    } else {
      onSelectionChange([])
    }
  }

  const allSelected = stocksWithData.length > 0 && selectedStocks.length === stocksWithData.length

  const formatCurrency = (value: number | null | undefined) => {
    if (value === null || value === undefined) return "N/A"
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value)
  }

  const formatNumber = (value: number | null | undefined) => {
    if (value === null || value === undefined) return "N/A"
    if (value >= 1_000_000_000) {
      return `${(value / 1_000_000_000).toFixed(2)}B`
    }
    if (value >= 1_000_000) {
      return `${(value / 1_000_000).toFixed(2)}M`
    }
    if (value >= 1_000) {
      return `${(value / 1_000).toFixed(2)}K`
    }
    return value.toLocaleString()
  }

  const formatPercent = (value: number | null | undefined) => {
    if (value === null || value === undefined) return "N/A"
    const sign = value >= 0 ? "+" : ""
    return `${sign}${value.toFixed(2)}%`
  }

  if (stocksWithData.length === 0) {
    return (
      <div className="rounded-md border p-8 text-center">
        <p className="text-muted-foreground">
          {stocks.length === 0
            ? "No stocks found. Add your first stock to get started!"
            : "No stocks match your filters. Try adjusting your search or filters."}
        </p>
      </div>
    )
  }

  return (
    <>
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              {onSelectionChange && (
                <TableHead className="w-12">
                  <Checkbox
                    checked={allSelected}
                    onCheckedChange={handleSelectAll}
                    aria-label="Select all"
                  />
                </TableHead>
              )}
              <TableHead className="cursor-pointer hover:bg-muted/50">
                Symbol
              </TableHead>
              <TableHead className="cursor-pointer hover:bg-muted/50">
                Name
              </TableHead>
              <TableHead className="cursor-pointer hover:bg-muted/50">
                Exchange
              </TableHead>
              <TableHead className="cursor-pointer hover:bg-muted/50">
                Sector
              </TableHead>
              <TableHead className="text-right">Price</TableHead>
              <TableHead className="text-right">Change</TableHead>
              <TableHead className="text-right">Volume</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {stocksWithData.map((stock) => {
              const isSelected = selectedStocks.some((s) => s.id === stock.id)
              const liveData = stock.liveData
              const isLoading = stock.isLoadingData

              return (
                <TableRow
                  key={stock.id}
                  data-state={isSelected ? "selected" : undefined}
                  className={isSelected ? "bg-muted/50" : ""}
                >
                  {onSelectionChange && (
                    <TableCell>
                      <Checkbox
                        checked={isSelected}
                        onCheckedChange={(checked) =>
                          handleSelectStock(stock, checked as boolean)
                        }
                        aria-label={`Select ${stock.symbol}`}
                      />
                    </TableCell>
                  )}
                  <TableCell>
                    <Button
                      variant="link"
                      className="h-auto p-0 font-mono font-semibold"
                      onClick={() => router.push(`/stocks/${stock.symbol}`)}
                    >
                      {stock.symbol}
                    </Button>
                  </TableCell>
                  <TableCell className="max-w-[200px] truncate">
                    {stock.name}
                  </TableCell>
                  <TableCell>{stock.exchange}</TableCell>
                  <TableCell>{stock.sector || "—"}</TableCell>
                  <TableCell className="text-right font-mono">
                    {isLoading ? (
                      <span className="text-muted-foreground">Loading...</span>
                    ) : liveData ? (
                      formatCurrency(liveData.current_price)
                    ) : (
                      <span className="text-muted-foreground">N/A</span>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    {isLoading ? (
                      <span className="text-muted-foreground">Loading...</span>
                    ) : liveData ? (
                      <div className="flex items-center justify-end gap-1 font-mono">
                        {liveData.change_percent >= 0 ? (
                          <TrendingUp className="h-4 w-4 text-green-600" />
                        ) : (
                          <TrendingDown className="h-4 w-4 text-red-600" />
                        )}
                        <span
                          className={
                            liveData.change_percent >= 0
                              ? "text-green-600"
                              : "text-red-600"
                          }
                        >
                          {formatPercent(liveData.change_percent)}
                        </span>
                      </div>
                    ) : (
                      <span className="text-muted-foreground">N/A</span>
                    )}
                  </TableCell>
                  <TableCell className="text-right font-mono text-sm">
                    {isLoading ? (
                      <span className="text-muted-foreground">Loading...</span>
                    ) : liveData ? (
                      formatNumber(liveData.volume)
                    ) : (
                      <span className="text-muted-foreground">N/A</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-amber-400 hover:text-amber-300"
                        onClick={() => toggleWatchlist(stock.symbol)}
                        aria-label={
                          isInWatchlist(stock.symbol)
                            ? `Remove ${stock.symbol} from watchlist`
                            : `Add ${stock.symbol} to watchlist`
                        }
                      >
                        {isInWatchlist(stock.symbol) ? (
                          <Star size={16} className="fill-current" />
                        ) : (
                          <StarOff size={16} />
                        )}
                      </Button>
                      {onEdit && (
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={() => setEditingStock(stock)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                      )}
                      {onDelete && (
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-destructive hover:text-destructive"
                          onClick={() => setDeletingStock(stock)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </div>

      {editingStock && (
        <EditStockDialog
          open={!!editingStock}
          onOpenChange={(open) => !open && setEditingStock(null)}
          stock={editingStock}
          onSuccess={() => {
            setEditingStock(null)
            onEdit?.(editingStock)
          }}
        />
      )}

      {deletingStock && (
        <DeleteStockDialog
          open={!!deletingStock}
          onOpenChange={(open) => !open && setDeletingStock(null)}
          stock={deletingStock}
          onSuccess={() => {
            setDeletingStock(null)
            onDelete?.(deletingStock)
          }}
        />
      )}
    </>
  )
}
