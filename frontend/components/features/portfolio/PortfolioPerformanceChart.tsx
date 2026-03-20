"use client"

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts"
import { getPortfolioHistory } from "@/lib/api/portfolio"

const PERIODS = [
  { label: "1D", value: "1d" },
  { label: "1W", value: "1w" },
  { label: "1M", value: "1m" },
  { label: "6M", value: "6m" },
  { label: "1Y", value: "1y" },
  { label: "ALL", value: "all" },
]

function formatXAxis(ts: number, period: string): string {
  const d = new Date(ts)
  if (period === "1d") return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
  if (period === "all") return d.toLocaleDateString([], { month: "short", year: "2-digit" })
  return d.toLocaleDateString([], { month: "short", day: "numeric" })
}

function formatValue(n: number): string {
  if (Math.abs(n) >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`
  if (Math.abs(n) >= 1_000) return `$${(n / 1_000).toFixed(1)}K`
  return `$${n.toFixed(0)}`
}

interface PortfolioPerformanceChartProps {
  enabled?: boolean
}

export function PortfolioPerformanceChart({ enabled = true }: PortfolioPerformanceChartProps) {
  const [period, setPeriod] = useState("1m")

  const { data, isPending } = useQuery({
    queryKey: ["portfolio-history", period],
    queryFn: () => getPortfolioHistory(period),
    staleTime: 5 * 60_000,
    enabled,
  })

  const points = data?.data ?? []
  const isPositive =
    points.length >= 2 ? points[points.length - 1].value >= points[0].value : true
  const color = isPositive ? "#4ade80" : "#f87171"
  const gradientId = `portfolio-grad-${period}`

  if (!enabled) return null

  return (
    <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-zinc-300 uppercase tracking-wide">
          Portfolio Performance
        </h2>
        <div className="flex gap-1">
          {PERIODS.map((p) => (
            <button
              key={p.value}
              onClick={() => setPeriod(p.value)}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                period === p.value
                  ? "bg-zinc-700 text-white"
                  : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {isPending ? (
        <div className="h-48 w-full animate-pulse bg-zinc-800 rounded-lg" />
      ) : points.length === 0 ? (
        <div className="h-48 flex items-center justify-center text-zinc-500 text-sm">
          No history data. Add positions to track performance over time.
        </div>
      ) : (
        <div className="h-48 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={points} margin={{ top: 8, right: 8, left: 0, bottom: 24 }}>
              <defs>
                <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={color} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={color} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
              <XAxis
                dataKey="t"
                tickFormatter={(v: number) => formatXAxis(v, period)}
                tick={{ fill: "#71717a", fontSize: 10 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                domain={["auto", "auto"]}
                tick={{ fill: "#71717a", fontSize: 10 }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(v: number) => formatValue(v)}
                width={50}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#18181b",
                  border: "1px solid #3f3f46",
                  borderRadius: "8px",
                  fontSize: "11px",
                }}
                labelFormatter={(v) => formatXAxis(v as number, period)}
                formatter={(v) => [formatValue(v as number), "Value"]}
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke={color}
                strokeWidth={1.5}
                fill={`url(#${gradientId})`}
                dot={false}
                activeDot={{ r: 3 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
