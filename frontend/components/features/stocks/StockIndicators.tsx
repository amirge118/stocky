"use client"

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ComposedChart,
  Bar,
  AreaChart,
  Area,
} from "recharts"
import { getStockIndicators } from "@/lib/api/stocks"
import type { IndicatorPoint, MacdPoint, BollingerPoint } from "@/types/stock"

const PERIODS = [
  { label: "1M", value: "1m" },
  { label: "6M", value: "6m" },
  { label: "1Y", value: "1y" },
]

function formatXAxis(ts: number): string {
  return new Date(ts).toLocaleDateString([], { month: "short", day: "numeric" })
}

const tooltipStyle = {
  contentStyle: {
    backgroundColor: "#18181b",
    border: "1px solid #3f3f46",
    borderRadius: "8px",
    fontSize: "11px",
  },
  labelStyle: { color: "#a1a1aa" },
  itemStyle: { color: "#e4e4e7" },
}

function ChartSkeleton() {
  return <div className="h-20 w-full animate-pulse bg-zinc-800 rounded-lg" />
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <span className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500 mb-1 block">
      {children}
    </span>
  )
}

interface RsiChartProps {
  data: IndicatorPoint[]
}

function RsiChart({ data }: RsiChartProps) {
  const filtered = data.filter((p) => p.v !== null)
  if (filtered.length === 0) {
    return <div className="h-20 flex items-center justify-center text-zinc-600 text-xs">No RSI data</div>
  }
  return (
    <div className="h-20 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={filtered} margin={{ top: 2, right: 8, left: 0, bottom: 2 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
          <XAxis
            dataKey="t"
            tickFormatter={(v: number) => formatXAxis(v)}
            tick={{ fill: "#71717a", fontSize: 9 }}
            axisLine={false}
            tickLine={false}
            minTickGap={60}
          />
          <YAxis
            domain={[0, 100]}
            ticks={[0, 30, 70, 100]}
            tick={{ fill: "#71717a", fontSize: 9 }}
            axisLine={false}
            tickLine={false}
            width={28}
          />
          <Tooltip
            {...tooltipStyle}
            labelFormatter={(v) => formatXAxis(v as number)}
            formatter={(value) => {
              const v = typeof value === "number" ? value : Number(value)
              const n = Number.isFinite(v) ? v : 0
              return [n.toFixed(2), "RSI"]
            }}
          />
          <ReferenceLine y={70} stroke="#f87171" strokeDasharray="4 2" strokeWidth={1} />
          <ReferenceLine y={30} stroke="#4ade80" strokeDasharray="4 2" strokeWidth={1} />
          <Line
            type="monotone"
            dataKey="v"
            stroke="#f97316"
            strokeWidth={1.5}
            dot={false}
            activeDot={{ r: 3, strokeWidth: 0 }}
            name="RSI"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

interface MacdChartProps {
  data: MacdPoint[]
}

function MacdChart({ data }: MacdChartProps) {
  const filtered = data.filter((p) => p.macd !== null || p.signal !== null)
  if (filtered.length === 0) {
    return <div className="h-20 flex items-center justify-center text-zinc-600 text-xs">No MACD data</div>
  }
  return (
    <div className="h-20 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={filtered} margin={{ top: 2, right: 8, left: 0, bottom: 2 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
          <XAxis
            dataKey="t"
            tickFormatter={(v: number) => formatXAxis(v)}
            tick={{ fill: "#71717a", fontSize: 9 }}
            axisLine={false}
            tickLine={false}
            minTickGap={60}
          />
          <YAxis
            tick={{ fill: "#71717a", fontSize: 9 }}
            axisLine={false}
            tickLine={false}
            width={28}
          />
          <Tooltip
            {...tooltipStyle}
            labelFormatter={(v) => formatXAxis(v as number)}
            formatter={(value, name) => {
              const v = typeof value === "number" ? value : Number(value)
              const n = Number.isFinite(v) ? v : 0
              return [n.toFixed(4), String(name ?? "")]
            }}
          />
          <ReferenceLine y={0} stroke="#3f3f46" strokeWidth={1} />
          <Bar
            dataKey="hist"
            name="Histogram"
            fill="#4ade80"
            radius={[1, 1, 0, 0]}
            // Color bars individually via a custom cell approach isn't needed —
            // we'll use a fixed color and rely on the sign being visible from the chart shape
          />
          <Line
            type="monotone"
            dataKey="macd"
            stroke="#3b82f6"
            strokeWidth={1.5}
            dot={false}
            activeDot={{ r: 3, strokeWidth: 0 }}
            name="MACD"
          />
          <Line
            type="monotone"
            dataKey="signal"
            stroke="#f97316"
            strokeWidth={1.5}
            dot={false}
            activeDot={{ r: 3, strokeWidth: 0 }}
            name="Signal"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}

interface BollingerChartProps {
  data: BollingerPoint[]
}

function BollingerChart({ data }: BollingerChartProps) {
  const filtered = data.filter((p) => p.middle !== null)
  if (filtered.length === 0) {
    return <div className="h-20 flex items-center justify-center text-zinc-600 text-xs">No Bollinger data</div>
  }

  // Build recharts data with upper/lower as area bounds
  const chartData = filtered.map((p) => ({
    t: p.t,
    upper: p.upper,
    middle: p.middle,
    lower: p.lower,
    // band is [lower, upper] rendered as area
    band: p.upper !== null && p.lower !== null ? [p.lower, p.upper] as [number, number] : null,
  }))

  return (
    <div className="h-20 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 2, right: 8, left: 0, bottom: 2 }}>
          <defs>
            <linearGradient id="bollinger-band" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.12} />
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.04} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
          <XAxis
            dataKey="t"
            tickFormatter={(v: number) => formatXAxis(v)}
            tick={{ fill: "#71717a", fontSize: 9 }}
            axisLine={false}
            tickLine={false}
            minTickGap={60}
          />
          <YAxis
            domain={["auto", "auto"]}
            tick={{ fill: "#71717a", fontSize: 9 }}
            axisLine={false}
            tickLine={false}
            width={40}
            tickFormatter={(v: number) => `$${v.toFixed(0)}`}
          />
          <Tooltip
            {...tooltipStyle}
            labelFormatter={(v) => formatXAxis(v as number)}
            formatter={(value, name) => {
              const v = typeof value === "number" ? value : Number(value)
              const n = Number.isFinite(v) ? v : 0
              return [`$${n.toFixed(2)}`, String(name ?? "")]
            }}
          />
          {/* Shaded band: upper as top boundary */}
          <Area
            type="monotone"
            dataKey="upper"
            stroke="#71717a"
            strokeWidth={1}
            strokeDasharray="4 2"
            fill="url(#bollinger-band)"
            dot={false}
            activeDot={false}
            name="Upper"
          />
          {/* Lower boundary — fill to 0 but use same gradient so it looks like a band */}
          <Area
            type="monotone"
            dataKey="lower"
            stroke="#71717a"
            strokeWidth={1}
            strokeDasharray="4 2"
            fill="#18181b"
            dot={false}
            activeDot={false}
            name="Lower"
          />
          {/* Middle SMA line on top */}
          <Area
            type="monotone"
            dataKey="middle"
            stroke="#3b82f6"
            strokeWidth={1.5}
            fill="none"
            dot={false}
            activeDot={{ r: 3, strokeWidth: 0 }}
            name="SMA20"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

interface StockIndicatorsProps {
  symbol: string
}

export function StockIndicators({ symbol }: StockIndicatorsProps) {
  const [period, setPeriod] = useState("6m")

  const { data, isPending } = useQuery({
    queryKey: ["indicators", symbol, period],
    queryFn: () => getStockIndicators(symbol, period),
    staleTime: 5 * 60_000,
  })

  return (
    <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold text-zinc-200">Technical Indicators</span>
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

      {/* RSI */}
      <div>
        <SectionLabel>RSI (14)</SectionLabel>
        {isPending ? <ChartSkeleton /> : <RsiChart data={data?.rsi ?? []} />}
      </div>

      {/* MACD */}
      <div>
        <SectionLabel>MACD (12, 26, 9)</SectionLabel>
        {isPending ? <ChartSkeleton /> : <MacdChart data={data?.macd ?? []} />}
      </div>

      {/* Bollinger Bands */}
      <div>
        <SectionLabel>Bollinger Bands (20, 2)</SectionLabel>
        {isPending ? <ChartSkeleton /> : <BollingerChart data={data?.bollinger ?? []} />}
      </div>
    </div>
  )
}
