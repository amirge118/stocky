"use client"

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
      ? "text-emerald-400"
      : accent === "loss"
        ? "text-red-400"
        : "text-white"

  const dotColor =
    accent === "gain"
      ? "bg-emerald-400"
      : accent === "loss"
        ? "bg-red-400"
        : "bg-zinc-600"

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center gap-1.5">
        <span className={`inline-block w-1.5 h-1.5 rounded-full ${dotColor}`} />
        <span className="text-[11px] font-medium tracking-widest uppercase text-zinc-500">
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
    )
  }

  if (!summary) return null

  const isGain = summary.total_gain_loss >= 0
  const plAccent: "gain" | "loss" = isGain ? "gain" : "loss"

  // Gradient border shifts with P&L direction
  const gradientClass = isGain
    ? "bg-gradient-to-br from-emerald-500/30 via-zinc-800 to-zinc-900"
    : "bg-gradient-to-br from-red-500/20 via-zinc-800 to-zinc-900"

  return (
    <div className={`p-px rounded-2xl ${gradientClass}`}>
      <div className="rounded-2xl bg-zinc-950 px-6 py-5">
        {/* Top row: total value (hero) + divider + 3 stats */}
        <div className="grid grid-cols-2 gap-x-8 gap-y-5 sm:grid-cols-4 sm:divide-x sm:divide-zinc-800/60">
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
        </div>

        {/* Bottom: thin progress bar showing unrealized gain as % of cost */}
        {summary.total_cost > 0 && (
          <div className="mt-5 space-y-1">
            <div className="h-px w-full bg-zinc-800" />
            <div className="flex items-center justify-between pt-2">
              <span className="text-[11px] text-zinc-600 tracking-widest uppercase">
                Portfolio performance
              </span>
              <span className={`text-[11px] font-medium ${isGain ? "text-emerald-500" : "text-red-400"}`}>
                {fmtPct(summary.total_gain_loss_pct)} all-time
              </span>
            </div>
            <div className="h-1 w-full rounded-full bg-zinc-800 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-700 ${
                  isGain
                    ? "bg-gradient-to-r from-emerald-600 to-emerald-400"
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
