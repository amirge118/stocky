"use client"

import { useState } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { Plus, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { getPortfolio } from "@/lib/api/portfolio"
import { PortfolioSummaryCard } from "@/components/features/portfolio/PortfolioSummaryCard"
import { PortfolioTable } from "@/components/features/portfolio/PortfolioTable"
import { AddPositionDialog } from "@/components/features/portfolio/AddPositionDialog"

export default function PortfolioPage() {
  const [dialogOpen, setDialogOpen] = useState(false)
  const queryClient = useQueryClient()

  const { data, isPending, isFetching } = useQuery({
    queryKey: ["portfolio"],
    queryFn: getPortfolio,
    refetchInterval: 60_000,
  })

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
            {/* Live pulse indicator */}
            <div className="flex items-center gap-1.5 mr-1">
              {isFetching ? (
                <RefreshCw size={12} className="text-zinc-500 animate-spin" />
              ) : (
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-40" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
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

        {/* ── Dialog ───────────────────────────────────────────────────────── */}
        <AddPositionDialog
          open={dialogOpen}
          onOpenChange={setDialogOpen}
          onSuccess={() => queryClient.invalidateQueries({ queryKey: ["portfolio"] })}
        />
      </div>
    </div>
  )
}
