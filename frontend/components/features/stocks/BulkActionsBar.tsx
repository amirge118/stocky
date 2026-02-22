"use client"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import { Trash2, Star, StarOff } from "lucide-react"
import type { Stock } from "@/types/stock"
import { useWatchlist } from "@/lib/hooks/useWatchlist"

export interface BulkActionsBarProps {
  selectedStocks: Stock[]
  allStocks: Stock[]
  onSelectAll: () => void
  onDeselectAll: () => void
  onBulkDelete: (stocks: Stock[]) => void
  onBulkAddToWatchlist?: (stocks: Stock[]) => void
  onBulkRemoveFromWatchlist?: (stocks: Stock[]) => void
}

export function BulkActionsBar({
  selectedStocks,
  allStocks,
  onSelectAll,
  onDeselectAll,
  onBulkDelete,
  onBulkAddToWatchlist,
  onBulkRemoveFromWatchlist,
}: BulkActionsBarProps) {
  const { isInWatchlist, toggleWatchlist } = useWatchlist()
  const selectedCount = selectedStocks.length
  const allSelected = selectedCount === allStocks.length && allStocks.length > 0

  if (selectedCount === 0) {
    return null
  }

  const handleBulkWatchlistToggle = () => {
    if (!onBulkAddToWatchlist || !onBulkRemoveFromWatchlist) return

    const allInWatchlist = selectedStocks.every((stock) =>
      isInWatchlist(stock.symbol)
    )

    if (allInWatchlist) {
      // Only call the bulk handler, which will handle the toggle internally
      onBulkRemoveFromWatchlist(selectedStocks)
    } else {
      // Only call the bulk handler, which will handle the toggle internally
      onBulkAddToWatchlist(selectedStocks)
    }
  }

  const selectedSymbols = selectedStocks.map((s) => s.symbol).join(", ")

  return (
    <div className="flex items-center justify-between rounded-lg border bg-muted/50 p-4">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Checkbox
            checked={allSelected}
            onCheckedChange={(checked) => {
              if (checked) {
                onSelectAll()
              } else {
                onDeselectAll()
              }
            }}
          />
          <span className="text-sm font-medium">
            {selectedCount} stock{selectedCount > 1 ? "s" : ""} selected
          </span>
        </div>
        {selectedCount <= 5 && (
          <Badge variant="secondary" className="text-xs">
            {selectedSymbols}
          </Badge>
        )}
      </div>

      <div className="flex items-center gap-2">
        {onBulkAddToWatchlist && onBulkRemoveFromWatchlist && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleBulkWatchlistToggle}
          >
            {selectedStocks.every((s) => isInWatchlist(s.symbol)) ? (
              <>
                <StarOff className="mr-2 h-4 w-4" />
                Remove from Watchlist
              </>
            ) : (
              <>
                <Star className="mr-2 h-4 w-4" />
                Add to Watchlist
              </>
            )}
          </Button>
        )}
        <Button
          variant="destructive"
          size="sm"
          onClick={() => onBulkDelete(selectedStocks)}
        >
          <Trash2 className="mr-2 h-4 w-4" />
          Delete Selected
        </Button>
      </div>
    </div>
  )
}
