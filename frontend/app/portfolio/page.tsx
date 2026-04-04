"use client"

import { useState, useEffect } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { Plus, RefreshCw, TrendingUp, PieChart as PieChartIcon } from "lucide-react"
import { Button } from "@/components/ui/button"
import { getPortfolioSummary } from "@/lib/api/portfolio"
import { PortfolioSummaryCard } from "@/components/features/portfolio/PortfolioSummaryCard"
import { PortfolioTable } from "@/components/features/portfolio/PortfolioTable"
import { AddPositionDialog } from "@/components/features/portfolio/AddPositionDialog"
import { SectorAllocationChart } from "@/components/features/portfolio/SectorAllocationChart"
import { SectorBreakdownTable } from "@/components/features/portfolio/SectorBreakdownTable"
import { SectorTrendCard } from "@/components/features/portfolio/SectorTrendCard"

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
            <div className="flex items-center gap-3.5">
              <div className="h-10 w-10 rounded-xl bg-zinc-800 animate-pulse" />
              <div>
                <p className="text-[10px] font-semibold tracking-widest uppercase text-zinc-500 mb-0.5">
                  Equity Portfolio
                </p>
                <h1 className="text-2xl font-bold tracking-tight text-white leading-none">
                  Portfolio
                </h1>
              </div>
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
          <div className="flex items-center gap-3.5">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <TrendingUp size={18} className="text-white" />
            </div>
            <div>
              <p className="text-[10px] font-semibold tracking-widest uppercase text-zinc-500 mb-0.5">
                Equity Portfolio
              </p>
              <h1 className="text-2xl font-bold tracking-tight text-white leading-none">
                Portfolio
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-2.5 pb-0.5">
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-zinc-800/60 border border-zinc-700/40" suppressHydrationWarning>
              {isFetching ? (
                <RefreshCw size={10} className="text-zinc-500 animate-spin" />
              ) : (
                <span className="relative flex h-1.5 w-1.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-40" />
                  <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-green-500" />
                </span>
              )}
              <span className="text-[10px] text-zinc-400 font-medium">Live</span>
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
          <div className="rounded-2xl bg-zinc-900 border border-zinc-800 overflow-hidden">
            <div className="px-6 py-4 border-b border-zinc-800/60 flex items-center gap-2">
              <PieChartIcon size={16} className="text-indigo-400" />
              <h2 className="text-sm font-semibold text-zinc-200 uppercase tracking-wide">
                Sector Allocation
              </h2>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
                <SectorAllocationChart sectors={sectorData.sectors} totalValue={sectorData.total_value} />
                <SectorBreakdownTable sectors={sectorData.sectors} />
              </div>
            </div>
            <div className="px-6 pb-6">
              <div className="border-t border-zinc-800/60 pt-5">
                <div className="flex items-center gap-2 mb-4">
                  <TrendingUp size={14} className="text-zinc-500" />
                  <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wide">
                    Sector Trends
                  </span>
                </div>
                <SectorTrendCard sectors={sectorData.sectors} />
              </div>
            </div>
          </div>
        )}

        {/* ── Dialog ───────────────────────────────────────────────────────── */}
        <AddPositionDialog
          open={dialogOpen}
          onOpenChange={setDialogOpen}
          onSuccess={() => {
            queryClient.invalidateQueries({ queryKey: ["portfolio-summary"] })
            queryClient.invalidateQueries({ queryKey: ["portfolio-history"] })
          }}
        />
      </div>
    </div>
  )
}
