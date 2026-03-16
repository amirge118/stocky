"use client"

import { useQuery } from "@tanstack/react-query"
import { getCompareSummary } from "@/lib/api/stocks"

interface CompareAISummaryProps {
  symbols: string[]
}

export function CompareAISummary({ symbols }: CompareAISummaryProps) {
  const { data, isPending, error } = useQuery({
    queryKey: ["compare-summary", symbols],
    queryFn: () => getCompareSummary(symbols),
    staleTime: 30 * 60_000,
    enabled: symbols.length >= 2,
  })

  if (symbols.length < 2) return null

  if (isPending) {
    return (
      <div className="rounded-xl bg-zinc-900 border border-zinc-800 border-l-4 border-l-violet-500 p-5 animate-pulse">
        <div className="h-4 w-24 rounded bg-zinc-800 mb-3" />
        <div className="space-y-2">
          <div className="h-3 bg-zinc-800 rounded w-full" />
          <div className="h-3 bg-zinc-800 rounded w-5/6" />
          <div className="h-3 bg-zinc-800 rounded w-4/5" />
        </div>
      </div>
    )
  }

  if (error || !data) {
    return null
  }

  return (
    <div className="rounded-xl bg-zinc-900 border border-zinc-800 border-l-4 border-l-violet-500 p-5">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-violet-400 text-base leading-none">✦</span>
        <h3 className="text-xs font-semibold text-zinc-300 uppercase tracking-wide">
          AI Comparison
        </h3>
        <span className="text-[10px] text-zinc-600 ml-auto">Powered by Claude</span>
      </div>
      <p className="text-zinc-300 text-sm leading-relaxed">{data.summary}</p>
    </div>
  )
}
