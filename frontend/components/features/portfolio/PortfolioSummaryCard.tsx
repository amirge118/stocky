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

export function PortfolioSummaryCard({ summary, isPending }: Props) {
  if (isPending) {
    return (
      <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6">
        <div className="grid grid-cols-2 gap-6 sm:grid-cols-4">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="space-y-2">
              <div className="h-2.5 w-16 rounded-full bg-zinc-800 skeleton-shimmer" />
              <div className="h-7 w-28 rounded bg-zinc-800 skeleton-shimmer" />
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (!summary) return null

  const isGain = summary.total_gain_loss >= 0
  const plAccent = isGain ? "gain" : "loss"

  const hasDayData = summary.total_day_change != null || summary.total_day_change_pct != null
  const dayIsGain = summary.total_day_change != null ? summary.total_day_change >= 0 : true

  const withDayChange = summary.positions.filter(
    (p) => p.day_change != null || p.day_change_percent != null
  )
  const leaders = withDayChange
    .filter((p) => (p.day_change_percent ?? 0) > 0)
    .sort((a, b) => (b.day_change_percent ?? 0) - (a.day_change_percent ?? 0))
    .slice(0, 3)
  const losers = withDayChange
    .filter((p) => (p.day_change_percent ?? 0) < 0)
    .sort((a, b) => (a.day_change_percent ?? 0) - (b.day_change_percent ?? 0))
    .slice(0, 3)

  // Secondary stats
  const stats: { label: string; value: string; sub?: string; accent?: "gain" | "loss" }[] = [
    { label: "Cost Basis", value: fmtCompact(summary.total_cost) },
    {
      label: "Total Return",
      value: fmt(summary.total_gain_loss),
      sub: fmtPct(summary.total_gain_loss_pct),
      accent: plAccent as "gain" | "loss",
    },
    {
      label: "Positions",
      value: `${summary.positions.length}`,
      sub: summary.positions.length === 1 ? "holding" : "holdings",
    },
  ]

  if (hasDayData) {
    stats.push({
      label: "Today",
      value:
        summary.total_day_change != null
          ? `${summary.total_day_change >= 0 ? "+" : ""}${fmtCompact(summary.total_day_change)}`
          : "—",
      sub:
        summary.total_day_change_pct != null
          ? fmtPct(summary.total_day_change_pct)
          : undefined,
      accent: dayIsGain ? "gain" : "loss",
    })
  }

  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-900 overflow-hidden">
      {/* Hero row: total value */}
      <div className="px-6 pt-6 pb-5">
        <p className="text-[10px] font-semibold tracking-widest uppercase text-zinc-500 mb-1">
          Total Value
        </p>
        <div className="flex items-baseline gap-3">
          <span className="text-4xl font-bold tabular-nums tracking-tight text-white">
            {fmtCompact(summary.total_value)}
          </span>
          {summary.total_gain_loss_pct != null && (
            <span
              className={`text-sm font-semibold tabular-nums px-2 py-0.5 rounded-md ${
                isGain
                  ? "bg-green-400/10 text-green-400"
                  : "bg-red-400/10 text-red-400"
              }`}
            >
              {fmtPct(summary.total_gain_loss_pct)}
            </span>
          )}
        </div>
      </div>

      {/* Stats row */}
      <div className="px-6 pb-5">
        <div className={`grid gap-4 ${stats.length === 4 ? "grid-cols-2 sm:grid-cols-4" : "grid-cols-3"}`}>
          {stats.map((s) => {
            const color =
              s.accent === "gain"
                ? "text-green-400"
                : s.accent === "loss"
                  ? "text-red-400"
                  : "text-zinc-200"
            return (
              <div key={s.label} className="rounded-xl bg-zinc-800/40 px-4 py-3">
                <p className="text-[10px] font-semibold tracking-widest uppercase text-zinc-500 mb-1.5">
                  {s.label}
                </p>
                <p className={`text-base font-semibold tabular-nums ${color}`}>
                  {s.value}
                </p>
                {s.sub && (
                  <p className={`text-xs tabular-nums mt-0.5 ${color} opacity-60`}>
                    {s.sub}
                  </p>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Today's movers */}
      {(leaders.length > 0 || losers.length > 0) && (
        <div className="px-6 pb-5 pt-1 border-t border-zinc-800/60">
          <p className="text-[10px] font-semibold tracking-widest uppercase text-zinc-500 mb-2.5 mt-3">
            Today&apos;s movers
          </p>
          <div className="flex flex-wrap gap-1.5">
            {leaders.map((p) => (
              <Link
                key={p.symbol}
                href={`/stocks/${p.symbol}`}
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium bg-green-400/10 text-green-400 hover:bg-green-400/20 transition-colors tabular-nums"
              >
                {p.symbol} {fmtPct(p.day_change_percent ?? 0)}
              </Link>
            ))}
            {losers.map((p) => (
              <Link
                key={p.symbol}
                href={`/stocks/${p.symbol}`}
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium bg-red-400/10 text-red-400 hover:bg-red-400/20 transition-colors tabular-nums"
              >
                {p.symbol} {fmtPct(p.day_change_percent ?? 0)}
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Performance bar */}
      {summary.total_cost > 0 && (
        <div className="px-6 pb-5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-semibold tracking-widest uppercase text-zinc-500">
              Performance
            </span>
            <span className={`text-xs font-medium tabular-nums ${isGain ? "text-green-400" : "text-red-400"}`}>
              {fmtPct(summary.total_gain_loss_pct)} all-time
            </span>
          </div>
          <div className="h-1.5 w-full rounded-full bg-zinc-800 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-700 ${
                isGain
                  ? "bg-gradient-to-r from-green-600 to-green-400"
                  : "bg-gradient-to-r from-red-700 to-red-500"
              }`}
              style={{
                width: `${Math.min(100, Math.abs(summary.total_gain_loss_pct))}%`,
              }}
            />
          </div>
        </div>
      )}
    </div>
  )
}
