"use client"

import { useState, useEffect } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { Plus, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { getPortfolioSummary } from "@/lib/api/portfolio"
import { PortfolioSummaryCard } from "@/components/features/portfolio/PortfolioSummaryCard"
import { PortfolioTable } from "@/components/features/portfolio/PortfolioTable"
import { AddPositionDialog } from "@/components/features/portfolio/AddPositionDialog"
import { SectorAllocationChart } from "@/components/features/portfolio/SectorAllocationChart"
import { SectorBreakdownTable } from "@/components/features/portfolio/SectorBreakdownTable"
import { SectorTrendCard } from "@/components/features/portfolio/SectorTrendCard"
import { PortfolioNewsFeed } from "@/components/features/portfolio/PortfolioNewsFeed"

export default function PortfolioPage() {
  const [mounted, setMounted] = useState(false)
  const [dialogOpen, setDialogOpen] = useState(false)
  const queryClient = useQueryClient()

  useEffect(() => {
    setMounted(true)
  }, [])

  const { data: summaryData, isPending, isFetching, isError } = useQuery({
    queryKey: ["portfolio-summary"],
    queryFn: getPortfolioSummary,
    staleTime: Infinity,
    refetchOnWindowFocus: false,
  })

  const data = summaryData?.portfolio
  const sectorData = summaryData?.sector_breakdown

  // Render static skeleton on server and initial client to avoid hydration mismatch
  if (!mounted) {
    return (
      <div className="min-h-screen bg-zinc-950 text-white">
        <div className="max-w-5xl mx-auto px-4 py-8 space-y-5">
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="text-[11px] font-medium tracking-widest uppercase text-zinc-500 mb-1">
                Equity Portfolio
              </p>
              <h1 className="text-3xl font-bold tracking-tight text-white leading-none">
                Portfolio
              </h1>
            </div>
            <div className="h-8 w-24 rounded bg-zinc-800 animate-pulse" />
          </div>
          <div className="p-px rounded-2xl bg-zinc-800">
            <div className="rounded-2xl bg-zinc-950 p-6 animate-pulse">
              <div className="grid grid-cols-2 gap-6 sm:grid-cols-4">
                {[0, 1, 2, 3].map((i) => (
                  <div key={i} className="space-y-2">
                    <div className="h-2.5 w-16 rounded-full bg-zinc-800" />
                    <div className="h-7 w-28 rounded bg-zinc-800" />
                  </div>
                ))}
              </div>
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

  if (isError) {
    return (
      <div className="min-h-screen bg-zinc-950 text-white flex items-center justify-center">
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900 px-10 py-12 text-center max-w-sm">
          <p className="text-zinc-200 font-semibold text-lg mb-2">Failed to load portfolio</p>
          <p className="text-zinc-500 text-sm mb-6">Could not reach the server. Check your connection and try again.</p>
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
      <div className="max-w-5xl mx-auto px-4 py-8 space-y-5">

        {/* ── Header ────────────────────────────────────────────────────────── */}
        <div className="flex items-end justify-between gap-4">
          <div>
            {/* Eyebrow */}
            <p className="text-[11px] font-medium tracking-widest uppercase text-zinc-500 mb-1">
              Equity Portfolio
            </p>
            {/* Headline */}
            <h1 className="text-3xl font-bold tracking-tight text-white leading-none">
              Portfolio
            </h1>
          </div>

          <div className="flex items-center gap-2 pb-0.5">
            {/* Live pulse indicator - suppressHydrationWarning: isFetching can differ server vs client */}
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
              onClick={() => setDialogOpen(true)}
              className="h-8 px-3 text-xs font-semibold bg-white text-zinc-950 hover:bg-zinc-100 rounded-lg gap-1.5"
            >
              <Plus size={13} />
              Add Position
            </Button>
          </div>
        </div>

        {/* ── Summary card ─────────────────────────────────────────────────── */}
        <PortfolioSummaryCard summary={data} isPending={isPending} />

        {/* ── Holdings table ───────────────────────────────────────────────── */}
        <PortfolioTable positions={data?.positions ?? []} isPending={isPending} />

        {/* ── Sector Breakdown ─────────────────────────────────────────────── */}
        {sectorData && sectorData.sectors.length > 0 && (
          <div className="space-y-4">
            <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-5 space-y-4">
              <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wide">
                Sector Allocation
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-center">
                <SectorAllocationChart sectors={sectorData.sectors} />
                <SectorBreakdownTable sectors={sectorData.sectors} />
              </div>
            </div>
            <SectorTrendCard sectors={sectorData.sectors} />
          </div>
        )}

        {/* ── Portfolio News Feed ──────────────────────────────────────────── */}
        {data && data.positions.length > 0 && (
          <PortfolioNewsFeed />
        )}

        {/* ── Dialog ───────────────────────────────────────────────────────── */}
        <AddPositionDialog
          open={dialogOpen}
          onOpenChange={setDialogOpen}
          onSuccess={() => {
            queryClient.invalidateQueries({ queryKey: ["portfolio-summary"] })
            queryClient.invalidateQueries({ queryKey: ["portfolio-news"] })
          }}
        />
      </div>
    </div>
  )
}
