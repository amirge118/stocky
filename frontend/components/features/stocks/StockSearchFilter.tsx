"use client"

import { useState, useMemo, useEffect, useRef } from "react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { X, Search } from "lucide-react"
import type { Stock } from "@/types/stock"

export interface StockSearchFilterProps {
  stocks: Stock[]
  searchQuery: string
  onSearchChange: (query: string) => void
  exchangeFilter?: string
  onExchangeFilterChange: (exchange: string | undefined) => void
  sectorFilter?: string
  onSectorFilterChange: (sector: string | undefined) => void
  watchlistOnly: boolean
  onWatchlistOnlyChange: (watchlistOnly: boolean) => void
}

export function StockSearchFilter({
  stocks,
  searchQuery,
  onSearchChange,
  exchangeFilter,
  onExchangeFilterChange,
  sectorFilter,
  onSectorFilterChange,
  watchlistOnly,
  onWatchlistOnlyChange,
}: StockSearchFilterProps) {
  const [localSearchQuery, setLocalSearchQuery] = useState(searchQuery)
  const timeoutRef = useRef<NodeJS.Timeout | undefined>(undefined)

  // Get unique exchanges and sectors from stocks
  const { exchanges, sectors } = useMemo(() => {
    const uniqueExchanges = Array.from(
      new Set(stocks.map((s) => s.exchange).filter((e): e is string => e !== null && e !== ""))
    ).sort()
    const uniqueSectors = Array.from(
      new Set(stocks.map((s) => s.sector).filter((s): s is string => s !== null && s !== ""))
    ).sort()
    return { exchanges: uniqueExchanges, sectors: uniqueSectors }
  }, [stocks])

  // Debounced search
  useEffect(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    timeoutRef.current = setTimeout(() => {
      onSearchChange(localSearchQuery)
    }, 300)

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [localSearchQuery, onSearchChange])

  const handleSearchChange = (value: string) => {
    setLocalSearchQuery(value)
  }

  const clearSearch = () => {
    setLocalSearchQuery("")
    onSearchChange("")
  }

  const clearAllFilters = () => {
    setLocalSearchQuery("")
    onSearchChange("")
    onExchangeFilterChange(undefined)
    onSectorFilterChange(undefined)
    onWatchlistOnlyChange(false)
  }

  const hasActiveFilters =
    searchQuery || exchangeFilter || sectorFilter || watchlistOnly

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
        {/* Search Input */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search by symbol, name, exchange, or sector..."
            value={localSearchQuery}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="pl-9 pr-9"
          />
          {localSearchQuery && (
            <Button
              variant="ghost"
              size="icon"
              className="absolute right-1 top-1/2 h-7 w-7 -translate-y-1/2"
              onClick={clearSearch}
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>

        {/* Exchange Filter */}
        <Select
          value={exchangeFilter || "all"}
          onValueChange={(value) =>
            onExchangeFilterChange(value === "all" ? undefined : value)
          }
        >
          <SelectTrigger className="w-full sm:w-[180px]">
            <SelectValue placeholder="All Exchanges" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Exchanges</SelectItem>
            {exchanges
              .filter((exchange) => exchange && exchange.trim() !== "")
              .map((exchange) => (
                <SelectItem key={exchange} value={exchange}>
                  {exchange}
                </SelectItem>
              ))}
          </SelectContent>
        </Select>

        {/* Sector Filter */}
        {sectors.length > 0 && (
          <Select
            value={sectorFilter || "all"}
            onValueChange={(value) =>
              onSectorFilterChange(value === "all" ? undefined : value)
            }
          >
            <SelectTrigger className="w-full sm:w-[180px]">
              <SelectValue placeholder="All Sectors" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Sectors</SelectItem>
              {sectors
                .filter((sector) => sector && sector.trim() !== "")
                .map((sector) => (
                  <SelectItem key={sector} value={sector}>
                    {sector}
                  </SelectItem>
                ))}
            </SelectContent>
          </Select>
        )}

        {/* Watchlist Toggle */}
        <Button
          variant={watchlistOnly ? "default" : "outline"}
          onClick={() => onWatchlistOnlyChange(!watchlistOnly)}
          className="w-full sm:w-auto"
        >
          {watchlistOnly ? "⭐ Watchlist" : "⭐ All Stocks"}
        </Button>
      </div>

      {/* Active Filters */}
      {hasActiveFilters && (
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm text-muted-foreground">Active filters:</span>
          {searchQuery && (
            <Badge variant="secondary" className="gap-1">
              Search: {searchQuery}
              <Button
                variant="ghost"
                size="icon"
                className="h-4 w-4 p-0 hover:bg-transparent"
                onClick={clearSearch}
              >
                <X className="h-3 w-3" />
              </Button>
            </Badge>
          )}
          {exchangeFilter && (
            <Badge variant="secondary" className="gap-1">
              Exchange: {exchangeFilter}
              <Button
                variant="ghost"
                size="icon"
                className="h-4 w-4 p-0 hover:bg-transparent"
                onClick={() => onExchangeFilterChange(undefined)}
              >
                <X className="h-3 w-3" />
              </Button>
            </Badge>
          )}
          {sectorFilter && (
            <Badge variant="secondary" className="gap-1">
              Sector: {sectorFilter}
              <Button
                variant="ghost"
                size="icon"
                className="h-4 w-4 p-0 hover:bg-transparent"
                onClick={() => onSectorFilterChange(undefined)}
              >
                <X className="h-3 w-3" />
              </Button>
            </Badge>
          )}
          {watchlistOnly && (
            <Badge variant="secondary" className="gap-1">
              Watchlist Only
              <Button
                variant="ghost"
                size="icon"
                className="h-4 w-4 p-0 hover:bg-transparent"
                onClick={() => onWatchlistOnlyChange(false)}
              >
                <X className="h-3 w-3" />
              </Button>
            </Badge>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={clearAllFilters}
            className="h-6 text-xs"
          >
            Clear all
          </Button>
        </div>
      )}
    </div>
  )
}
