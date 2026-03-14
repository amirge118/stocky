"use client"

import type { StockInfoResponse } from "@/types/stock"


function formatMarketCap(v: number | null): string {
  if (v == null) return "—"
  if (v >= 1e12) return `$${(v / 1e12).toFixed(2)}T`
  if (v >= 1e9) return `$${(v / 1e9).toFixed(2)}B`
  if (v >= 1e6) return `$${(v / 1e6).toFixed(2)}M`
  return `$${v.toLocaleString()}`
}

function fmt2(v: number | null): string {
  return v != null ? v.toFixed(2) : "—"
}

function fmtPct(v: number | null): string {
  if (v == null) return "—"
  return `${(v * 100).toFixed(2)}%`
}

function fmtVol(v: number | null): string {
  if (v == null) return "—"
  if (v >= 1e9) return `${(v / 1e9).toFixed(1)}B`
  if (v >= 1e6) return `${(v / 1e6).toFixed(1)}M`
  if (v >= 1e3) return `${(v / 1e3).toFixed(0)}K`
  return v.toLocaleString()
}

const StatRow = ({
  label,
  value,
  compact,
}: {
  label: string
  value: string
  compact?: boolean
}) =>
  compact ? (
    <div className="flex items-center gap-2">
      <span className="text-zinc-500 text-xs">{label}:</span>
      <span className="text-white font-medium text-xs">{value}</span>
    </div>
  ) : (
    <div className="flex justify-between items-center py-2 border-b border-zinc-800 last:border-0">
      <span className="text-zinc-400 text-sm">{label}</span>
      <span className="text-white font-medium text-sm">{value}</span>
    </div>
  )

const STATS = [
  { key: "market_cap", label: "Market Cap", fmt: (i: StockInfoResponse) => formatMarketCap(i.market_cap) },
  { key: "pe", label: "P/E", fmt: (i: StockInfoResponse) => fmt2(i.pe_ratio) },
  { key: "fpe", label: "Fwd P/E", fmt: (i: StockInfoResponse) => fmt2(i.forward_pe) },
  { key: "beta", label: "Beta", fmt: (i: StockInfoResponse) => fmt2(i.beta) },
  { key: "52h", label: "52W High", fmt: (i: StockInfoResponse) => (i.fifty_two_week_high != null ? `$${i.fifty_two_week_high.toFixed(2)}` : "—") },
  { key: "52l", label: "52W Low", fmt: (i: StockInfoResponse) => (i.fifty_two_week_low != null ? `$${i.fifty_two_week_low.toFixed(2)}` : "—") },
  { key: "vol", label: "Avg Vol", fmt: (i: StockInfoResponse) => fmtVol(i.average_volume) },
  { key: "div", label: "Div Yield", fmt: (i: StockInfoResponse) => fmtPct(i.dividend_yield) },
] as const

interface StockKeyStatsProps {
  info: StockInfoResponse
  compact?: boolean
}

export function StockKeyStats({ info, compact = false }: StockKeyStatsProps) {
  if (compact) {
    return (
      <div className="rounded-xl bg-zinc-900 border border-zinc-800 px-4 py-3">
        <h2 className="text-xs font-semibold text-zinc-400 uppercase tracking-wide mb-2">Key Statistics</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-x-6 gap-y-1.5">
          {STATS.map((s) => (
            <StatRow key={s.key} label={s.label} value={s.fmt(info)} compact />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-5">
      <h2 className="text-sm font-semibold text-zinc-300 uppercase tracking-wide mb-3">Key Statistics</h2>
      {STATS.map((s) => (
        <StatRow key={s.key} label={s.label} value={s.fmt(info)} />
      ))}
    </div>
  )
}
