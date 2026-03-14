"use client"

import { useQueries } from "@tanstack/react-query"
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts"
import { getStockHistory } from "@/lib/api/stocks"
import type { StockHistoryPoint } from "@/types/stock"

interface StockComparisonChartProps {
  symbols: string[]
  colors: string[]
}

function formatXAxis(ts: number): string {
  return new Date(ts).toLocaleDateString([], { month: "short", day: "numeric" })
}

export function StockComparisonChart({ symbols, colors }: StockComparisonChartProps) {
  const queries = useQueries({
    queries: symbols.map((symbol) => ({
      queryKey: ["history", symbol, "1m"],
      queryFn: () => getStockHistory(symbol, "1m"),
      staleTime: 60_000,
    })),
  })

  const isLoading = queries.some((q) => q.isPending)
  const allData = queries.map((q) => q.data?.data ?? [])

  if (isLoading) {
    return (
      <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-6 animate-pulse">
        <div className="h-64 rounded bg-zinc-800" />
      </div>
    )
  }

  const hasData = allData.some((arr) => arr.length > 0)
  if (!hasData) {
    return (
      <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-12 text-center">
        <p className="text-zinc-500">No chart data available for the selected symbols</p>
      </div>
    )
  }

  const allTimestamps = new Set<number>()
  allData.forEach((points) => points.forEach((p) => allTimestamps.add(p.t)))
  const sortedTimestamps = Array.from(allTimestamps).sort((a, b) => a - b)

  const getPriceAt = (points: StockHistoryPoint[], t: number): number | null => {
    const exact = points.find((p) => p.t === t)
    if (exact) return exact.c
    const before = points.filter((p) => p.t <= t).sort((a, b) => b.t - a.t)[0]
    const after = points.filter((p) => p.t >= t).sort((a, b) => a.t - b.t)[0]
    if (before && after) {
      const frac = (t - before.t) / (after.t - before.t)
      return before.c + frac * (after.c - before.c)
    }
    return before?.c ?? after?.c ?? null
  }

  const firstPrices = allData.map((points) => {
    const first = points[0]
    return first ? first.c : 1
  })

  const chartData = sortedTimestamps.map((t) => {
    const row: Record<string, number | string> = { t }
    symbols.forEach((sym, i) => {
      const price = getPriceAt(allData[i], t)
      if (price !== null && firstPrices[i] > 0) {
        const pctChange = ((price - firstPrices[i]) / firstPrices[i]) * 100
        row[sym] = parseFloat(pctChange.toFixed(2))
      }
    })
    return row
  })

  return (
    <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-4">
      <p className="text-xs text-zinc-500 mb-3">Normalized to % change from start (1M)</p>
      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 24 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
            <XAxis
              dataKey="t"
              tickFormatter={formatXAxis}
              tick={{ fill: "#71717a", fontSize: 10 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              domain={["auto", "auto"]}
              tick={{ fill: "#71717a", fontSize: 10 }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v: number) => `${v}%`}
              width={40}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#18181b",
                border: "1px solid #3f3f46",
                borderRadius: "8px",
                fontSize: "11px",
              }}
              labelFormatter={(v) => formatXAxis(v as number)}
              formatter={(value: number | undefined) => [value != null ? `${value}%` : "", ""]}
            />
            <Legend
              wrapperStyle={{ fontSize: "11px" }}
              formatter={(value) => <span className="text-zinc-300">{value}</span>}
            />
            {symbols.map((sym, i) => (
              <Area
                key={sym}
                type="monotone"
                dataKey={sym}
                stroke={colors[i % colors.length]}
                strokeWidth={1.5}
                fill={colors[i % colors.length]}
                fillOpacity={0.15}
                dot={false}
                activeDot={{ r: 3 }}
              />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
