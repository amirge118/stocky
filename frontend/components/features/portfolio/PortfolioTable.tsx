"use client"

import { useRouter } from "next/navigation"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { X, TrendingUp, TrendingDown, Download } from "lucide-react"
import { Button } from "@/components/ui/button"
import { removeHolding } from "@/lib/api/portfolio"
import type { PortfolioPosition } from "@/types/portfolio"

interface Props {
  positions: PortfolioPosition[]
  isPending: boolean
}

function fmtUSD(n: number | null, decimals = 2): string {
  if (n === null) return "—"
  return n.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

function fmtPct(n: number | null): string {
  if (n === null) return "—"
  return `${n >= 0 ? "+" : ""}${n.toFixed(2)}%`
}

function GainLossPill({ value, pct }: { value: number | null; pct: number | null }) {
  if (value === null) return <span className="text-zinc-600 text-xs">—</span>
  const isUp = value >= 0
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-medium tabular-nums ${
        isUp
          ? "bg-emerald-400/10 text-emerald-400"
          : "bg-red-400/10 text-red-400"
      }`}
    >
      {isUp ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
      {fmtPct(pct)}
    </span>
  )
}

function PortfolioBar({ pct }: { pct: number | null }) {
  if (pct === null) return null
  return (
    <div className="flex items-center gap-2">
      <div className="h-1 w-16 rounded-full bg-zinc-800 overflow-hidden">
        <div
          className="h-full rounded-full bg-blue-500/60"
          style={{ width: `${Math.min(100, pct)}%` }}
        />
      </div>
      <span className="text-zinc-400 tabular-nums text-xs">{pct.toFixed(1)}%</span>
    </div>
  )
}

function positionsToCSV(positions: PortfolioPosition[]): string {
  const headers = [
    "Symbol",
    "Name",
    "Shares",
    "Avg Cost",
    "Current Price",
    "Market Value",
    "Total Cost",
    "Gain/Loss",
    "Gain/Loss %",
    "Portfolio %",
  ]
  const rows = positions.map((pos) => [
    pos.symbol,
    `"${(pos.name || "").replace(/"/g, '""')}"`,
    pos.shares.toFixed(2),
    pos.avg_cost.toFixed(2),
    pos.current_price != null ? pos.current_price.toFixed(2) : "",
    pos.current_value != null ? pos.current_value.toFixed(2) : "",
    pos.total_cost.toFixed(2),
    pos.gain_loss != null ? pos.gain_loss.toFixed(2) : "",
    pos.gain_loss_pct != null ? pos.gain_loss_pct.toFixed(2) : "",
    pos.portfolio_pct != null ? pos.portfolio_pct.toFixed(2) : "",
  ])
  return [headers.join(","), ...rows.map((r) => r.join(","))].join("\n")
}

export function PortfolioTable({ positions, isPending }: Props) {
  const router = useRouter()
  const queryClient = useQueryClient()

  const handleExportCSV = () => {
    const csv = positionsToCSV(positions)
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `portfolio-${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  const removeMutation = useMutation({
    mutationFn: removeHolding,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["portfolio"] }),
  })

  if (isPending) {
    return (
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
    )
  }

  if (positions.length === 0) {
    return (
      <div className="rounded-2xl border border-zinc-800 bg-zinc-900/30 px-8 py-16 text-center">
        <div className="mx-auto mb-3 w-10 h-10 rounded-full bg-zinc-800 flex items-center justify-center">
          <TrendingUp size={18} className="text-zinc-600" />
        </div>
        <p className="text-zinc-400 font-medium">No positions yet</p>
        <p className="text-zinc-600 text-sm mt-1">Add your first stock to get started</p>
      </div>
    )
  }

  return (
    <div className="rounded-2xl border border-zinc-800 overflow-hidden">
      {/* Table header strip */}
      <div className="bg-zinc-900/50 px-5 py-2.5 border-b border-zinc-800 flex items-center justify-between">
        <span className="text-[11px] font-medium tracking-widest uppercase text-zinc-500">
          Holdings
        </span>
        <div className="flex items-center gap-3">
          <span className="text-[11px] text-zinc-600">
            {positions.length} position{positions.length !== 1 ? "s" : ""}
          </span>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleExportCSV}
            className="h-7 text-xs text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800"
          >
            <Download size={12} className="mr-1" />
            Export CSV
          </Button>
        </div>
      </div>

      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-zinc-800/60">
            {["Symbol", "Shares", "Avg Cost", "Price", "Market Value", "Return", "Weight", ""].map(
              (col, i) => (
                <th
                  key={i}
                  className={`px-5 py-2.5 text-[11px] font-medium tracking-widest uppercase text-zinc-600 bg-zinc-900/30 ${
                    i === 0 ? "text-left" : i === 7 ? "w-10" : "text-right"
                  }`}
                >
                  {col}
                </th>
              )
            )}
          </tr>
        </thead>
        <tbody>
          {positions.map((pos, idx) => {
            const isUp = pos.gain_loss !== null ? pos.gain_loss >= 0 : null
            const priceColor =
              isUp === true
                ? "text-emerald-400"
                : isUp === false
                  ? "text-red-400"
                  : "text-zinc-300"

            return (
              <tr
                key={pos.symbol}
                onClick={() => router.push(`/stocks/${pos.symbol}`)}
                className={`
                  group cursor-pointer transition-colors duration-100
                  border-b border-zinc-800/40 last:border-0
                  hover:bg-zinc-800/40
                  ${idx % 2 === 0 ? "bg-zinc-950" : "bg-zinc-900/20"}
                `}
              >
                {/* Symbol + Name */}
                <td className="px-5 py-3.5">
                  <div className="flex items-center gap-3">
                    {/* Accent dot shows gain/loss direction */}
                    <span
                      className={`w-1 h-8 rounded-full shrink-0 transition-colors ${
                        isUp === true
                          ? "bg-emerald-500/50 group-hover:bg-emerald-400"
                          : isUp === false
                            ? "bg-red-500/50 group-hover:bg-red-400"
                            : "bg-zinc-700"
                      }`}
                    />
                    <div>
                      <div className="font-mono font-bold text-white tracking-wide">
                        {pos.symbol}
                      </div>
                      <div className="text-[11px] text-zinc-500 truncate max-w-[160px] mt-0.5">
                        {pos.name}
                      </div>
                    </div>
                  </div>
                </td>

                {/* Shares */}
                <td className="px-5 py-3.5 text-right">
                  <span className="tabular-nums text-zinc-300 font-medium">
                    {pos.shares.toLocaleString("en-US")}
                  </span>
                </td>

                {/* Avg Cost */}
                <td className="px-5 py-3.5 text-right">
                  <span className="tabular-nums font-mono text-zinc-400 text-xs">
                    {fmtUSD(pos.avg_cost, 2)}
                  </span>
                </td>

                {/* Current Price */}
                <td className="px-5 py-3.5 text-right">
                  <span className={`tabular-nums font-mono font-semibold ${priceColor}`}>
                    {fmtUSD(pos.current_price)}
                  </span>
                </td>

                {/* Market Value */}
                <td className="px-5 py-3.5 text-right">
                  <span className="tabular-nums text-white font-medium">
                    {fmtUSD(pos.current_value)}
                  </span>
                  <div className="text-[11px] text-zinc-600 tabular-nums">
                    {fmtUSD(pos.gain_loss)} P&amp;L
                  </div>
                </td>

                {/* Return pill */}
                <td className="px-5 py-3.5 text-right">
                  <GainLossPill value={pos.gain_loss} pct={pos.gain_loss_pct} />
                </td>

                {/* Weight bar */}
                <td className="px-5 py-3.5 text-right">
                  <PortfolioBar pct={pos.portfolio_pct} />
                </td>

                {/* Remove */}
                <td
                  className="px-3 py-3.5"
                  onClick={(e) => e.stopPropagation()}
                >
                  <Button
                    size="icon"
                    variant="ghost"
                    className="h-7 w-7 opacity-0 group-hover:opacity-100 text-zinc-600 hover:text-red-400 hover:bg-red-400/10 transition-all"
                    disabled={removeMutation.isPending}
                    onClick={() => removeMutation.mutate(pos.symbol)}
                  >
                    <X className="h-3.5 w-3.5" />
                  </Button>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
