"use client"

import { useState, useEffect } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { Plus, RefreshCw, TrendingUp, PieChart as PieChartIcon } from "lucide-react"
import { Button } from "@/components/ui/button"
import { getPortfolioSummary, getPortfolioNews } from "@/lib/api/portfolio"
import { ApiError } from "@/lib/api/client"
import { PortfolioSummaryCard } from "@/components/features/portfolio/PortfolioSummaryCard"
import { PortfolioTable } from "@/components/features/portfolio/PortfolioTable"
import { AddPositionDialog } from "@/components/features/portfolio/AddPositionDialog"
import { SectorAllocationChart } from "@/components/features/portfolio/SectorAllocationChart"
import { SectorBreakdownTable } from "@/components/features/portfolio/SectorBreakdownTable"
import { SectorTrendCard } from "@/components/features/portfolio/SectorTrendCard"
import { PortfolioNewsFeed } from "@/components/features/portfolio/PortfolioNewsFeed"
import type { PortfolioNewsItem } from "@/types/portfolio"

export default function PortfolioPage() {
  const [mounted, setMounted] = useState(false)
  const [dialogOpen, setDialogOpen] = useState(false)
  const queryClient = useQueryClient()

  useEffect(() => {
    setMounted(true)
  }, [])

  const { data: summaryData, isPending, isFetching, isError, error, failureCount } = useQuery({
    queryKey: ["portfolio-summary"],
    queryFn: getPortfolioSummary,
    staleTime: 60_000,
    refetchOnWindowFocus: false,
    retry: (count, err) => {
      // Retry 500/502/503 up to 12× (~60s) — Render free tier cold starts can return any of these
      if (err instanceof ApiError && (err.status === 500 || err.status === 502 || err.status === 503)) {
        return count < 12
      }
      return false
    },
    retryDelay: 5000,
  })

  const data = summaryData?.portfolio
  const sectorData = summaryData?.sector_breakdown
  const hasPositions = (data?.positions.length ?? 0) > 0

  const { data: newsItems, isPending: newsPending } = useQuery({
    queryKey: ["portfolio-news", 50],
    queryFn: () => getPortfolioNews(50),
    staleTime: 5 * 60_000,
    enabled: hasPositions,
  })

  const headlineBySymbol: Record<string, PortfolioNewsItem> = {}
  if (newsItems?.length && data?.positions.length) {
    const want = new Set(data.positions.map((p) => p.symbol))
    for (const item of newsItems) {
      if (!want.has(item.symbol)) continue
      if (!headlineBySymbol[item.symbol]) headlineBySymbol[item.symbol] = item
    }
  }

  const handleRefreshPortfolio = () => {
    queryClient.invalidateQueries({ queryKey: ["portfolio-summary"] })
    queryClient.invalidateQueries({ queryKey: ["portfolio-news"] })
  }

  if (!mounted) {
    return (
      <div className="min-h-screen bg-zinc-950 text-white">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-6">
          <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-4 min-w-0">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-violet-500/20 bg-violet-500/10">
                <TrendingUp className="h-5 w-5 text-violet-300" aria-hidden />
              </div>
              <div className="min-w-0">
                <p className="text-[10px] font-semibold tracking-[0.22em] uppercase text-zinc-500">
                  Equity Portfolio
                </p>
                <h1 className="mt-1 text-2xl sm:text-3xl font-bold tracking-tight text-white">
                  Portfolio
                </h1>
              </div>
            </div>
            <div className="h-9 w-32 rounded-lg bg-zinc-800 animate-pulse shrink-0" />
          </div>
          <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-6 sm:p-7 animate-pulse">
            <div className="grid grid-cols-2 gap-8 md:grid-cols-3 xl:grid-cols-5">
              {[0, 1, 2, 3, 4].map((i) => (
                <div key={i} className="min-w-0 space-y-2">
                  <div className="h-2.5 w-16 rounded-full bg-zinc-800" />
                  <div className="h-8 w-24 max-w-full rounded bg-zinc-800" />
                </div>
              ))}
            </div>
          </div>
          <div className="rounded-2xl border border-zinc-800 overflow-hidden">
            <div className="bg-zinc-900/50 px-5 py-3 border-b border-zinc-800">
              <div className="h-3 w-20 rounded-full bg-zinc-800 animate-pulse" />
            </div>
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className="flex items-center gap-4 px-5 py-4 border-b border-zinc-800/60 animate-pulse"
              >
                <div className="h-4 w-12 rounded bg-zinc-800" />
                <div className="h-3 w-32 rounded bg-zinc-800" />
                <div className="ml-auto h-4 w-20 rounded bg-zinc-800" />
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  // isPending + failureCount > 0 means retrying (TanStack narrows error to null when isPending)
  const isRetrying = isPending && failureCount > 0
  // After all retries, check if the final error was a cold-start 502/503
  const isColdStart = isError && error instanceof ApiError && (error.status === 502 || error.status === 503)

  if (isRetrying) {
    // Show warming-up state during auto-retry
    return (
      <div className="min-h-screen bg-zinc-950 text-white flex items-center justify-center">
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900 px-10 py-12 text-center max-w-sm space-y-3">
          <RefreshCw size={20} className="mx-auto text-zinc-500 animate-spin" />
          <p className="text-zinc-200 font-semibold text-lg">Backend is warming up</p>
          <p className="text-zinc-500 text-sm">
            The server is starting from sleep. This takes ~20–30 seconds on the free tier.
          </p>
          <p className="text-zinc-600 text-xs">Retrying automatically… (attempt {failureCount} of 12)</p>
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="min-h-screen bg-zinc-950 text-white flex items-center justify-center">
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900 px-10 py-12 text-center max-w-sm space-y-3">
          <p className="text-zinc-200 font-semibold text-lg">Failed to load portfolio</p>
          <p className="text-zinc-500 text-sm">
            {isColdStart
              ? "The backend didn't respond in time. It may still be starting — try again in a moment."
              : "Could not reach the server. Check your connection and try again."}
          </p>
          <Button
            onClick={() => queryClient.invalidateQueries({ queryKey: ["portfolio-summary"] })}
            className="h-8 px-4 text-xs font-semibold bg-white text-zinc-950 hover:bg-zinc-100 rounded-lg"
          >
            <RefreshCw size={12} className="mr-1.5" />
            Retry
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-6">

        <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-4 min-w-0">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-violet-500/20 bg-violet-500/10">
              <TrendingUp className="h-5 w-5 text-violet-300" aria-hidden />
            </div>
            <div className="min-w-0">
              <p className="text-[10px] font-semibold tracking-[0.22em] uppercase text-zinc-500">
                Equity Portfolio
              </p>
              <h1 className="mt-1 text-2xl sm:text-3xl font-bold tracking-tight text-white">
                Portfolio
              </h1>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2 shrink-0">
            <div className="flex items-center gap-1.5 mr-1" suppressHydrationWarning>
              {isFetching ? (
                <RefreshCw size={12} className="text-zinc-500 animate-spin" />
              ) : (
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-40" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500" />
                </span>
              )}
              <span className="text-[11px] text-zinc-600 tracking-wide">Live</span>
            </div>

            <Button
              type="button"
              variant="outline"
              onClick={handleRefreshPortfolio}
              className="h-8 px-3 text-xs font-semibold border-zinc-700 bg-zinc-900 text-zinc-200 hover:bg-zinc-800 rounded-lg gap-1.5"
            >
              <RefreshCw size={13} />
              Refresh
            </Button>

            <Button
              onClick={() => setDialogOpen(true)}
              className="h-8 px-3 text-xs font-semibold bg-white text-zinc-950 hover:bg-zinc-100 rounded-lg gap-1.5"
            >
              <Plus size={13} />
              Add Position
            </Button>
          </div>
        </div>

        <PortfolioSummaryCard summary={data} isPending={isPending} />

        <PortfolioTable
          positions={data?.positions ?? []}
          isPending={isPending}
          headlineBySymbol={headlineBySymbol}
        />

        {sectorData && sectorData.sectors.length > 0 && (
          <div className="rounded-2xl border border-zinc-800 bg-zinc-900 overflow-hidden">
            <div className="flex items-center gap-2 border-b border-zinc-800/60 px-6 py-4">
              <PieChartIcon size={16} className="text-indigo-400" />
              <h2 className="text-sm font-semibold tracking-wide text-zinc-200 uppercase">
                Sector Allocation
              </h2>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 items-center gap-8 md:grid-cols-2">
                <SectorAllocationChart
                  sectors={sectorData.sectors}
                  totalValue={sectorData.total_value}
                />
                <SectorBreakdownTable sectors={sectorData.sectors} />
              </div>
            </div>
            <div className="px-6 pb-6">
              <div className="border-t border-zinc-800/60 pt-5">
                <div className="mb-4 flex items-center gap-2">
                  <TrendingUp size={14} className="text-zinc-500" />
                  <span className="text-xs font-semibold tracking-wide text-zinc-400 uppercase">
                    Sector Trends
                  </span>
                </div>
                <SectorTrendCard sectors={sectorData.sectors} />
              </div>
            </div>
          </div>
        )}

        {data && data.positions.length > 0 && (
          <PortfolioNewsFeed items={newsItems} isPending={newsPending} />
        )}

        <AddPositionDialog
          open={dialogOpen}
          onOpenChange={setDialogOpen}
          onSuccess={() => {
            queryClient.invalidateQueries({ queryKey: ["portfolio-summary"] })
            queryClient.invalidateQueries({ queryKey: ["portfolio-news"] })
            queryClient.invalidateQueries({ queryKey: ["portfolio-history"] })
          }}
        />
      </div>
    </div>
  )
}
