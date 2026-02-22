"use client"

import { useQuery } from "@tanstack/react-query"
import { getStockAnalysis } from "@/lib/api/stocks"

interface StockAIAnalysisProps {
  symbol: string
}

export function StockAIAnalysis({ symbol }: StockAIAnalysisProps) {
  const { data, isPending, error } = useQuery({
    queryKey: ["analysis", symbol],
    queryFn: () => getStockAnalysis(symbol),
    staleTime: 30 * 60_000,
    retry: 1,
  })

  return (
    <div className="rounded-xl bg-zinc-900 border border-zinc-800 border-l-4 border-l-violet-500 p-5">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-violet-400 text-base leading-none">✦</span>
        <h2 className="text-sm font-semibold text-zinc-300 uppercase tracking-wide">AI Analysis</h2>
        <span className="text-xs text-zinc-600 ml-auto">Powered by Claude</span>
      </div>

      {isPending ? (
        <div className="space-y-2 animate-pulse">
          <div className="h-3 bg-zinc-800 rounded w-full" />
          <div className="h-3 bg-zinc-800 rounded w-5/6" />
          <div className="h-3 bg-zinc-800 rounded w-4/5" />
          <div className="h-3 bg-zinc-800 rounded w-11/12" />
        </div>
      ) : error ? (
        <p className="text-zinc-500 text-sm">Analysis unavailable at this time.</p>
      ) : (
        <p className="text-zinc-300 text-sm leading-relaxed">{data?.analysis}</p>
      )}
    </div>
  )
}
