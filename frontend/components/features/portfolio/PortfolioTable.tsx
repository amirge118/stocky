"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { X, TrendingUp, TrendingDown, Download, Bell, ChevronUp, ChevronDown } from "lucide-react"
import { Button } from "@/components/ui/button"
import { removeHolding } from "@/lib/api/portfolio"
import { fetchAlerts } from "@/lib/api/alerts"
import type { PortfolioPosition, PortfolioSummaryWithSector } from "@/types/portfolio"
import type { Alert } from "@/types/alerts"

interface Props {
  positions: PortfolioPosition[]
  isPending: boolean
}

type SortCol =
  | "symbol"
  | "shares"
  | "avg_cost"
  | "current_price"
  | "day_change_percent"
  | "current_value"
  | "gain_loss_pct"
  | "portfolio_pct"

const COLUMNS: { label: string; key: SortCol | null; align: "left" | "right" }[] = [
  { label: "Symbol",       key: "symbol",             align: "left" },
  { label: "Shares",       key: "shares",             align: "right" },
  { label: "Avg Cost",     key: "avg_cost",           align: "right" },
  { label: "Price",        key: "current_price",      align: "right" },
  { label: "Day %",        key: "day_change_percent", align: "right" },
  { label: "Market Value", key: "current_value",      align: "right" },
  { label: "Return",       key: "gain_loss_pct",      align: "right" },
  { label: "Weight",       key: "portfolio_pct",      align: "right" },
  { label: "",             key: null,                 align: "right" },
]

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
          ? "bg-green-400/10 text-green-400"
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
    "Day Change %",
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
    pos.day_change_percent != null ? pos.day_change_percent.toFixed(2) : "",
    pos.current_value != null ? pos.current_value.toFixed(2) : "",
    pos.total_cost.toFixed(2),
    pos.gain_loss != null ? pos.gain_loss.toFixed(2) : "",
    pos.gain_loss_pct != null ? pos.gain_loss_pct.toFixed(2) : "",
    pos.portfolio_pct != null ? pos.portfolio_pct.toFixed(2) : "",
  ])
  return [headers.join(","), ...rows.map((r) => r.join(","))].join("\n")
}

function sortPositions(
  positions: PortfolioPosition[],
  col: SortCol,
  dir: "asc" | "desc"
): PortfolioPosition[] {
  return [...positions].sort((a, b) => {
    const aVal = a[col as keyof PortfolioPosition]
    const bVal = b[col as keyof PortfolioPosition]

    if (aVal === null || aVal === undefined) return 1
    if (bVal === null || bVal === undefined) return -1

    let cmp = 0
    if (typeof aVal === "string" && typeof bVal === "string") {
      cmp = aVal.localeCompare(bVal)
    } else {
      cmp = (aVal as number) - (bVal as number)
    }
    return dir === "asc" ? cmp : -cmp
  })
}

export function PortfolioTable({ positions, isPending }: Props) {
  const router = useRouter()
  const queryClient = useQueryClient()
  const [sort, setSort] = useState<{ col: SortCol; dir: "asc" | "desc" }>({
    col: "symbol",
    dir: "asc",
  })

  const { data: alerts = [] } = useQuery({
    queryKey: ["alerts"],
    queryFn: () => fetchAlerts(50, 0),
    staleTime: 30_000,
  })

  const alertsByTicker: Record<string, Alert[]> = {}
  for (const alert of alerts) {
    if (!alert.is_active) continue
    if (!alertsByTicker[alert.ticker]) alertsByTicker[alert.ticker] = []
    alertsByTicker[alert.ticker].push(alert)
  }

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
    onMutate: async (symbol) => {
      await queryClient.cancelQueries({ queryKey: ["portfolio-summary"] })
      const previous = queryClient.getQueryData<PortfolioSummaryWithSector>(["portfolio-summary"])
      queryClient.setQueryData<PortfolioSummaryWithSector>(["portfolio-summary"], (old) => {
        if (!old) return old
        const p = old.portfolio
        const newPositions = p.positions.filter((pos) => pos.symbol !== symbol)
        return {
          ...old,
          portfolio: {
            ...p,
            positions: newPositions,
          },
        }
      })
      return { previous }
    },
    onError: (_err, _symbol, context) => {
      if (context?.previous) {
        queryClient.setQueryData(["portfolio-summary"], context.previous)
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["portfolio-summary"] })
      queryClient.invalidateQueries({ queryKey: ["portfolio-history"] })
      queryClient.invalidateQueries({ queryKey: ["portfolio-news"] })
    },
  })

  if (isPending) {
    return (
      <div className="rounded-2xl border border-zinc-800 overflow-hidden">
        <div className="bg-zinc-900/50 px-5 py-3 border-b border-zinc-800">
          <div className="h-3 w-20 rounded-full bg-zinc-800 skeleton-shimmer" />
        </div>
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="flex items-center gap-4 px-5 py-4 border-b border-zinc-800/60"
          >
            <div className="h-4 w-12 rounded bg-zinc-800 skeleton-shimmer" />
            <div className="h-3 w-32 rounded bg-zinc-800 skeleton-shimmer" />
            <div className="ml-auto h-4 w-20 rounded bg-zinc-800 skeleton-shimmer" />
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

  const sortedPositions = sortPositions(positions, sort.col, sort.dir)

  const handleSort = (key: SortCol | null) => {
    if (!key) return
    setSort((prev) =>
      prev.col === key
        ? { col: key, dir: prev.dir === "asc" ? "desc" : "asc" }
        : { col: key, dir: "asc" }
    )
  }

  return (
    <div className="rounded-2xl border border-zinc-800 overflow-hidden">
      {/* Table header strip */}
      <div className="bg-zinc-900/50 px-5 py-2.5 border-b border-zinc-800 flex items-center justify-between">
        <span className="text-xs font-medium tracking-widest uppercase text-zinc-500">
          Holdings
        </span>
        <div className="flex items-center gap-3">
          <span className="text-xs text-zinc-600">
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
            {COLUMNS.map((col, i) => (
              <th
                key={i}
                onClick={() => handleSort(col.key)}
                className={`px-5 py-2.5 text-xs font-medium tracking-widest uppercase text-zinc-600 bg-zinc-900/30 select-none ${
                  col.align === "left" ? "text-left" : i === COLUMNS.length - 1 ? "w-10" : "text-right"
                } ${col.key ? "cursor-pointer hover:text-zinc-400 transition-colors" : ""}`}
              >
                <span className="inline-flex items-center gap-1">
                  {col.label}
                  {col.key && sort.col === col.key && (
                    sort.dir === "asc"
                      ? <ChevronUp size={11} className="text-zinc-400" />
                      : <ChevronDown size={11} className="text-zinc-400" />
                  )}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sortedPositions.map((pos, idx) => {
            const isUp = pos.gain_loss !== null ? pos.gain_loss >= 0 : null
            const priceColor =
              isUp === true
                ? "text-green-400"
                : isUp === false
                  ? "text-red-400"
                  : "text-zinc-300"
            const activeAlertsForPos = alertsByTicker[pos.symbol] ?? []

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
                          ? "bg-green-500/50 group-hover:bg-green-400"
                          : isUp === false
                            ? "bg-red-500/50 group-hover:bg-red-400"
                            : "bg-zinc-700"
                      }`}
                    />
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="font-mono font-bold text-white tracking-wide">
                          {pos.symbol}
                        </span>
                        {activeAlertsForPos.length > 0 && (
                          <span
                            className="inline-flex items-center gap-0.5 text-amber-400"
                            title={`${activeAlertsForPos.length} active alert${activeAlertsForPos.length !== 1 ? "s" : ""}`}
                            onClick={(e) => {
                              e.stopPropagation()
                              router.push(`/stocks/${pos.symbol}?tab=alerts`)
                            }}
                          >
                            <Bell size={11} />
                            <span className="text-[10px] font-semibold tabular-nums">
                              {activeAlertsForPos.length}
                            </span>
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-zinc-500 truncate max-w-[160px] mt-0.5">
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

                {/* Day Change */}
                <td className="px-5 py-3.5 text-right">
                  {pos.day_change_percent != null ? (
                    <span
                      className={`tabular-nums text-xs font-medium ${
                        pos.day_change_percent >= 0
                          ? "text-green-400"
                          : "text-red-400"
                      }`}
                    >
                      {pos.day_change_percent >= 0 ? "+" : ""}
                      {pos.day_change_percent.toFixed(2)}%
                    </span>
                  ) : (
                    <span className="text-zinc-600 text-xs">—</span>
                  )}
                </td>

                {/* Market Value */}
                <td className="px-5 py-3.5 text-right">
                  <span className="tabular-nums text-white font-medium">
                    {fmtUSD(pos.current_value)}
                  </span>
                  <div className="text-xs text-zinc-600 tabular-nums">
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
