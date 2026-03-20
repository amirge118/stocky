"use client"

import { useQuery } from "@tanstack/react-query"
import { getMarketOverview } from "@/lib/api/market"
import { IndicesStrip } from "@/components/features/market/IndicesStrip"
import { SectorHeatmap } from "@/components/features/market/SectorHeatmap"
import { TopMovers } from "@/components/features/market/TopMovers"
import { YourMovers } from "@/components/features/market/YourMovers"

const FIVE_MINUTES = 5 * 60 * 1000

function MarketSkeleton() {
  return (
    <div className="space-y-8 animate-pulse">
      {/* Indices skeleton */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-zinc-900 border border-zinc-800 rounded-lg h-24" />
        ))}
      </div>
      {/* Sector heatmap skeleton */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
        {[...Array(11)].map((_, i) => (
          <div key={i} className="bg-zinc-900 border border-zinc-800 rounded-lg h-16" />
        ))}
      </div>
      {/* Movers skeleton */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg h-56" />
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg h-56" />
      </div>
    </div>
  )
}

export default function MarketPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["marketOverview"],
    queryFn: getMarketOverview,
    staleTime: FIVE_MINUTES,
    refetchInterval: FIVE_MINUTES,
  })

  return (
    <main className="max-w-5xl mx-auto px-4 py-6 space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">Market Pulse</h1>
        {data && (
          <span className="text-xs text-zinc-500">
            Updated {new Date(data.updated_at).toLocaleTimeString()}
          </span>
        )}
      </div>

      {isLoading && <MarketSkeleton />}

      {isError && (
        <div className="bg-red-950/40 border border-red-800 rounded-lg p-6 text-center">
          <p className="text-red-400 font-medium">Failed to load market data.</p>
          <p className="text-red-500 text-sm mt-1">Please try again in a moment.</p>
        </div>
      )}

      {data && (
        <>
          <IndicesStrip indices={data.indices} />
          <SectorHeatmap sectors={data.sectors} />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <YourMovers />
            <TopMovers gainers={data.gainers} losers={data.losers} />
          </div>
        </>
      )}
    </main>
  )
}
