"use client"

import { TrendingUp, TrendingDown } from "lucide-react"
import { useStockPrices } from "@/lib/hooks/useStockPrices"

interface LivePriceBadgeProps {
  symbol: string
  fallbackPrice?: number
  fallbackChange?: number
  fallbackChangePercent?: number
  currency?: string
}

export function LivePriceBadge({
  symbol,
  fallbackPrice,
  fallbackChange,
  fallbackChangePercent,
  currency = "USD",
}: LivePriceBadgeProps) {
  const prices = useStockPrices([symbol])
  const live = prices[symbol]

  const price = live?.price ?? fallbackPrice
  const change = live?.change ?? fallbackChange ?? 0
  const changePercent = live?.change_percent ?? fallbackChangePercent ?? 0
  const isPositive = change >= 0

  if (price == null) return null

  return (
    <span
      className={`inline-flex items-center gap-1 text-sm font-medium px-2 py-0.5 rounded-md ${
        isPositive ? "text-green-400 bg-green-400/10" : "text-red-400 bg-red-400/10"
      }`}
    >
      {isPositive ? <TrendingUp size={13} /> : <TrendingDown size={13} />}
      {currency === "ILS" ? "₪" : "$"}{price.toFixed(2)}
      <span className="opacity-80">
        ({isPositive ? "+" : ""}
        {change.toFixed(2)} / {isPositive ? "+" : ""}
        {changePercent.toFixed(2)}%)
      </span>
    </span>
  )
}
