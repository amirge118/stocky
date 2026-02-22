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

const StatRow = ({ label, value }: { label: string; value: string }) => (
  <div className="flex justify-between items-center py-2 border-b border-zinc-800 last:border-0">
    <span className="text-zinc-400 text-sm">{label}</span>
    <span className="text-white font-medium text-sm">{value}</span>
  </div>
)

interface StockKeyStatsProps {
  info: StockInfoResponse
}

export function StockKeyStats({ info }: StockKeyStatsProps) {
  return (
    <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-5">
      <h2 className="text-sm font-semibold text-zinc-300 uppercase tracking-wide mb-3">Key Statistics</h2>
      <StatRow label="Market Cap" value={formatMarketCap(info.market_cap)} />
      <StatRow label="P/E Ratio (TTM)" value={fmt2(info.pe_ratio)} />
      <StatRow label="Forward P/E" value={fmt2(info.forward_pe)} />
      <StatRow label="Beta" value={fmt2(info.beta)} />
      <StatRow label="52W High" value={info.fifty_two_week_high != null ? `$${info.fifty_two_week_high.toFixed(2)}` : "—"} />
      <StatRow label="52W Low" value={info.fifty_two_week_low != null ? `$${info.fifty_two_week_low.toFixed(2)}` : "—"} />
      <StatRow label="Avg Volume" value={fmtVol(info.average_volume)} />
      <StatRow label="Dividend Yield" value={fmtPct(info.dividend_yield)} />
    </div>
  )
}
