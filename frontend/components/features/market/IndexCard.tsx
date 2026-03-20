import { Sparkline } from "@/components/features/stocks/Sparkline"
import type { IndexData } from "@/types/market"

interface IndexCardProps {
  index: IndexData
}

function formatPrice(price: number, symbol: string): string {
  if (symbol === "^VIX") return price.toFixed(2)
  if (price >= 10000) return price.toLocaleString("en-US", { maximumFractionDigits: 0 })
  return price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

export function IndexCard({ index }: IndexCardProps) {
  const isPositive = index.change_percent >= 0
  const changeColor = isPositive ? "text-green-400" : "text-red-400"
  const sign = isPositive ? "+" : ""

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 flex flex-col gap-2 min-w-0">
      <div className="flex items-start justify-between gap-2">
        <span className="text-xs text-zinc-400 font-medium truncate">{index.name}</span>
        <span className={`text-xs font-semibold shrink-0 ${changeColor}`}>
          {sign}{index.change_percent.toFixed(2)}%
        </span>
      </div>
      <div className="flex items-end justify-between gap-2">
        <span className="text-lg font-bold text-white tabular-nums leading-none">
          {formatPrice(index.price, index.symbol)}
        </span>
        {index.sparkline.length >= 2 && (
          <Sparkline data={index.sparkline} width={72} height={28} />
        )}
      </div>
      <div className={`text-xs tabular-nums ${changeColor}`}>
        {sign}{index.change.toFixed(2)} today
      </div>
    </div>
  )
}
