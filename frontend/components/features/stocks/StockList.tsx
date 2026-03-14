"use client"

import { useQuery } from "@tanstack/react-query"
import { getStocks } from "@/lib/api/stocks"
import { StockCard } from "./StockCard"
import { StockListSkeleton } from "@/components/shared/StockListSkeleton"
import { ErrorMessage } from "@/components/shared/ErrorMessage"

interface StockListProps {
  page?: number
  limit?: number
  onStockClick?: (symbol: string) => void
}

export function StockList({ page = 1, limit = 20, onStockClick }: StockListProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["stocks", page, limit],
    queryFn: () => getStocks({ page, limit }),
  })

  if (isLoading) {
    return <StockListSkeleton />
  }

  if (error) {
    return <ErrorMessage error={error} />
  }

  if (!data || data.data.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">No stocks found.</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {data.data.map((stock) => (
        <StockCard key={stock.id} stock={stock} onSelect={onStockClick} />
      ))}
    </div>
  )
}
