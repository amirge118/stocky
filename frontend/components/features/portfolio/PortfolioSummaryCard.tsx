"use client"

import Link from "next/link"
import type { PortfolioSummary } from "@/types/portfolio"

interface Props {
  summary: PortfolioSummary | undefined
  isPending: boolean
}

function fmt(n: number): string {
  return n.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
  })
}

function fmtCompact(n: number): string {
  if (Math.abs(n) >= 1_000_000)
    return `${n < 0 ? "-" : ""}$${(Math.abs(n) / 1_000_000).toFixed(2)}M`
  if (Math.abs(n) >= 1_000)
    return `${n < 0 ? "-" : ""}$${(Math.abs(n) / 1_000).toFixed(1)}K`
  return fmt(n)
}

function fmtPct(n: number): string {
  return `${n >= 0 ? "+" : ""}${n.toFixed(2)}%`
}

interface StatProps {
  label: string
  primary: string
  secondary?: string
  accent?: "gain" | "loss" | "neutral"
}

/** One summary tile: same typography and vertical rhythm as every other tile. */
function Stat({ label, primary, secondary, accent = "neutral" }: StatProps) {
  const accentColor =
    accent === "gain"
      ? "text-green-400"
      : accent === "loss"
        ? "text-red-400"
        : "text-white"

  const dotColor =
    accent === "gain"
      ? "bg-green-400"
      : accent === "loss"
        ? "bg-red-400"
        : "bg-zinc-600"

  const secondaryMuted =
    accent === "gain"
      ? "text-green-400/75"
      : accent === "loss"
        ? "text-red-400/75"
        : "text-zinc-500"

  return (
    <div className="flex h-full min-h-[6.5rem] flex-col justify-center gap-2 py-1">
      <div className="flex items-center gap-1.5">
        <span className={`inline-block size-1.5 shrink-0 rounded-full ${dotColor}`} />
        <span className="text-[11px] font-medium leading-none tracking-widest text-zinc-500 uppercase">
          {label}
        </span>
      </div>
      <p
        className={`font-semibold tabular-nums text-lg leading-tight tracking-tight sm:text-xl md:text-[1.65rem] ${accentColor}`}
      >
        {primary}
      </p>
      <p className={`min-h-[1.125rem] text-sm leading-tight tabular-nums ${secondaryMuted}`}>
        {secondary ?? "\u00a0"}
      </p>
    </div>
  )
}

export function PortfolioSummaryCard({ summary, isPending }: Props) {
  if (isPending) {
    return (
      <div className="overflow-hidden rounded-xl border border-zinc-800 bg-zinc-900/50 shadow-sm shadow-black/20">
        <div
          className="flex min-h-[6.75rem] w-full min-w-0 animate-pulse divide-x divide-zinc-800/90"
          aria-hidden
        >
          {[0, 1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="min-w-0 flex-1 basis-0 px-3 py-4 sm:px-4 sm:py-5"
            >
              <div className="space-y-2">
                <div className="h-2.5 w-14 max-w-full rounded-full bg-zinc-800/90 skeleton-shimmer" />
                <div className="h-8 max-w-[90%] rounded bg-zinc-800/90 skeleton-shimmer" />
                <div className="h-3.5 w-12 rounded bg-zinc-800/70 skeleton-shimmer" />
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (!summary) return null

  const isGain = summary.total_gain_loss >= 0
  const plAccent: "gain" | "loss" = isGain ? "gain" : "loss"

  const hasDayData = summary.total_day_change != null || summary.total_day_change_pct != null
  const dayAccent: "gain" | "loss" | "neutral" =
    summary.total_day_change != null
      ? summary.total_day_change >= 0
        ? "gain"
        : "loss"
      : "neutral"

  const withDayChange = positionsWithDayChange(summary.positions)
  const leaders = withDayChange
    .filter((p) => (p.day_change_percent ?? 0) > 0)
    .sort((a, b) => (b.day_change_percent ?? 0) - (a.day_change_percent ?? 0))
    .slice(0, 3)
  const losers = withDayChange
    .filter((p) => (p.day_change_percent ?? 0) < 0)
    .sort((a, b) => (a.day_change_percent ?? 0) - (b.day_change_percent ?? 0))
    .slice(0, 3)

  return (
    <div className="overflow-hidden rounded-xl border border-zinc-800 bg-zinc-950 shadow-sm shadow-black/20">
      {/* Single connected row: equal-width segments, hairline dividers only (no gaps). */}
      <div className="flex w-full min-w-0 flex-nowrap divide-x divide-zinc-800/90 overflow-x-auto bg-zinc-900/45 [-ms-overflow-style:none] [scrollbar-width:thin] [&::-webkit-scrollbar]:h-1 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-zinc-700">
        <div className="min-w-0 flex-1 basis-0 px-3 py-4 sm:px-4 sm:py-5">
          <Stat label="Total Value" primary={fmtCompact(summary.total_value)} />
        </div>
        <div className="min-w-0 flex-1 basis-0 px-3 py-4 sm:px-4 sm:py-5">
          <Stat label="Cost Basis" primary={fmtCompact(summary.total_cost)} />
        </div>
        <div className="min-w-0 flex-1 basis-0 px-3 py-4 sm:px-4 sm:py-5">
          <Stat
            label="Total Return"
            primary={fmt(summary.total_gain_loss)}
            secondary={fmtPct(summary.total_gain_loss_pct)}
            accent={plAccent}
          />
        </div>
        <div className="min-w-0 flex-1 basis-0 px-3 py-4 sm:px-4 sm:py-5">
          <Stat
            label="Positions"
            primary={`${summary.positions.length}`}
            secondary={summary.positions.length === 1 ? "holding" : "holdings"}
          />
        </div>
        {hasDayData && (
          <div className="min-w-0 flex-1 basis-0 px-3 py-4 sm:px-4 sm:py-5">
            <Stat
              label="Today"
              primary={
                summary.total_day_change != null
                  ? `${summary.total_day_change >= 0 ? "+" : ""}${fmtCompact(summary.total_day_change)}`
                  : "—"
              }
              secondary={
                summary.total_day_change_pct != null
                  ? fmtPct(summary.total_day_change_pct)
                  : undefined
              }
              accent={dayAccent}
            />
          </div>
        )}
      </div>

      {(leaders.length > 0 || losers.length > 0) && (
        <div className="border-t border-zinc-800/70 px-5 py-5 sm:px-6">
          <p className="mb-2 text-xs font-medium tracking-widest text-zinc-600 uppercase">
            Today&apos;s movers
          </p>
          <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm">
            {leaders.length > 0 && (
              <span className="flex items-center gap-2">
                <span className="text-zinc-500">Leaders:</span>
                {leaders.map((p) => (
                  <Link
                    key={p.symbol}
                    href={`/stocks/${p.symbol}`}
                    className="font-medium text-green-400 tabular-nums transition-colors hover:text-green-300"
                  >
                    {p.symbol} {fmtPct(p.day_change_percent ?? 0)} (
                    {p.day_change != null && p.day_change >= 0 ? "+" : ""}
                    {fmtCompact(p.day_change ?? 0)})
                  </Link>
                ))}
              </span>
            )}
            {leaders.length > 0 && losers.length > 0 && (
              <span className="text-zinc-700">|</span>
            )}
            {losers.length > 0 && (
              <span className="flex items-center gap-2">
                <span className="text-zinc-500">Losers:</span>
                {losers.map((p) => (
                  <Link
                    key={p.symbol}
                    href={`/stocks/${p.symbol}`}
                    className="font-medium text-red-400 tabular-nums transition-colors hover:text-red-300"
                  >
                    {p.symbol} {fmtPct(p.day_change_percent ?? 0)} (
                    {fmtCompact(p.day_change ?? 0)})
                  </Link>
                ))}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

function positionsWithDayChange(
  positions: PortfolioSummary["positions"]
): PortfolioSummary["positions"] {
  return positions.filter(
    (p) => p.day_change != null || p.day_change_percent != null
  )
}
