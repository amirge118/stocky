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
  large?: boolean
}

function Stat({ label, primary, secondary, accent = "neutral", large }: StatProps) {
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

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center gap-1.5">
        <span className={`inline-block w-1.5 h-1.5 rounded-full ${dotColor}`} />
        <span className="text-xs font-medium tracking-widest uppercase text-zinc-500">
          {label}
        </span>
      </div>
      <span
        className={`font-semibold tabular-nums leading-none ${accentColor} ${
          large ? "text-3xl tracking-tight" : "text-xl"
        }`}
      >
        {primary}
      </span>
      {secondary && (
        <span className={`text-sm tabular-nums ${accentColor} opacity-70`}>{secondary}</span>
      )}
    </div>
  )
}

export function PortfolioSummaryCard({ summary, isPending }: Props) {
  if (isPending) {
    return (
      <div className="p-px rounded-2xl bg-gradient-to-br from-zinc-700 via-zinc-800 to-zinc-900">
        <div className="rounded-2xl bg-zinc-950 p-6">
          <div className="grid grid-cols-2 gap-6 sm:grid-cols-4">
            {[0, 1, 2, 3].map((i) => (
              <div key={i} className="space-y-2">
                <div className="h-2.5 w-16 rounded-full bg-zinc-800 skeleton-shimmer" />
                <div className="h-7 w-28 rounded bg-zinc-800 skeleton-shimmer" />
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (!summary) return null

  const isGain = summary.total_gain_loss >= 0
  const plAccent: "gain" | "loss" = isGain ? "gain" : "loss"

  // Gradient border shifts with P&L direction
  const gradientClass = isGain
    ? "bg-gradient-to-br from-green-500/30 via-zinc-800 to-zinc-900"
    : "bg-gradient-to-br from-red-500/20 via-zinc-800 to-zinc-900"

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
    <div className={`p-px rounded-2xl ${gradientClass}`}>
      <div className="rounded-2xl bg-zinc-950 px-6 py-5">
        {/* Top row: total value + stats + optional Day P&L */}
        <div
          className={`grid gap-x-8 gap-y-5 sm:divide-x sm:divide-zinc-800/60 ${
            hasDayData
              ? "grid-cols-2 sm:grid-cols-5"
              : "grid-cols-2 sm:grid-cols-4"
          }`}
        >
          <Stat
            label="Total Value"
            primary={fmtCompact(summary.total_value)}
            large
          />
          <div className="sm:pl-8">
            <Stat
              label="Cost Basis"
              primary={fmtCompact(summary.total_cost)}
            />
          </div>
          <div className="sm:pl-8">
            <Stat
              label="Total Return"
              primary={fmt(summary.total_gain_loss)}
              secondary={fmtPct(summary.total_gain_loss_pct)}
              accent={plAccent}
            />
          </div>
          <div className="sm:pl-8">
            <Stat
              label="Positions"
              primary={`${summary.positions.length}`}
              secondary={summary.positions.length === 1 ? "holding" : "holdings"}
            />
          </div>
          {hasDayData && (
            <div className="sm:pl-8">
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

        {/* Today's Movers */}
        {(leaders.length > 0 || losers.length > 0) && (
          <div className="mt-4 pt-4 border-t border-zinc-800/60">
            <p className="text-xs font-medium tracking-widest uppercase text-zinc-600 mb-2">
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
                      className="text-green-400 hover:text-green-300 font-medium tabular-nums transition-colors"
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
                      className="text-red-400 hover:text-red-300 font-medium tabular-nums transition-colors"
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

        {/* Bottom: thin progress bar showing unrealized gain as % of cost */}
        {summary.total_cost > 0 && (
          <div className="mt-5 space-y-1">
            <div className="h-px w-full bg-zinc-800" />
            <div className="flex items-center justify-between pt-2">
              <span className="text-xs text-zinc-600 tracking-widest uppercase">
                Portfolio performance
              </span>
              <span className={`text-xs font-medium ${isGain ? "text-green-400" : "text-red-400"}`}>
                {fmtPct(summary.total_gain_loss_pct)} all-time
              </span>
            </div>
            <div className="h-1 w-full rounded-full bg-zinc-800 overflow-hidden">
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
