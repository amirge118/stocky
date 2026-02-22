"use client"

import { useState, useEffect, useRef } from "react"
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
import { getStockHistory } from "@/lib/api/stocks"
import type { StockHistoryPoint } from "@/types/stock"

const PERIODS = [
  { label: "1D", value: "1d" },
  { label: "1W", value: "1w" },
  { label: "1M", value: "1m" },
  { label: "6M", value: "6m" },
  { label: "1Y", value: "1y" },
]

function formatXAxis(ts: number, period: string): string {
  const d = new Date(ts)
  if (period === "1d") return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
  return d.toLocaleDateString([], { month: "short", day: "numeric" })
}

function formatTooltipDate(ts: number, period: string): string {
  const d = new Date(ts)
  if (period === "1d") return d.toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })
  return d.toLocaleDateString([], { month: "short", day: "numeric", year: "numeric" })
}

// Pure SVG candlestick drawn in real pixel coordinates (no viewBox distortion)
function CandlestickChart({ points }: { points: StockHistoryPoint[] }) {
  const svgRef = useRef<SVGSVGElement>(null)
  const [svgW, setSvgW] = useState(0)

  useEffect(() => {
    const el = svgRef.current
    if (!el) return
    const update = () => setSvgW(el.getBoundingClientRect().width)
    update()
    const ro = new ResizeObserver(update)
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  const svgH = 112 // matches h-28
  const padL = 4
  const padR = 46
  const padT = 8
  const padB = 6
  const chartW = svgW - padL - padR
  const chartH = svgH - padT - padB

  const allHighs = points.map((p) => p.h)
  const allLows = points.map((p) => p.l)
  const maxP = Math.max(...allHighs)
  const minP = Math.min(...allLows)
  const range = maxP - minP || 1
  const pMin = minP - range * 0.04
  const pMax = maxP + range * 0.04
  const pRange = pMax - pMin

  const py = (price: number) => padT + chartH - ((price - pMin) / pRange) * chartH
  const px = (i: number) => padL + (i + 0.5) * (chartW / points.length)
  const candleW = Math.max(1.5, (chartW / points.length) * 0.6)

  const tickCount = 3
  const ticks = Array.from({ length: tickCount }, (_, i) => {
    const price = pMin + (pRange * (i + 0.5)) / tickCount
    return { price, y: py(price) }
  })

  return (
    // No viewBox — draw directly in pixel space so nothing gets stretched
    <svg ref={svgRef} width="100%" height={svgH} style={{ display: "block" }}>
      {svgW > 0 && (
        <>
          {/* Grid lines */}
          {ticks.map((t, i) => (
            <line
              key={i}
              x1={padL}
              y1={t.y}
              x2={svgW - padR}
              y2={t.y}
              stroke="#27272a"
              strokeWidth={0.5}
            />
          ))}

          {/* Candles */}
          {points.map((p, i) => {
            const bullish = p.c >= p.o
            const color = bullish ? "#22c55e" : "#ef4444"
            const x = px(i)
            const bodyTop = py(Math.max(p.o, p.c))
            const bodyBot = py(Math.min(p.o, p.c))
            const bodyH = Math.max(1, bodyBot - bodyTop)
            return (
              <g key={p.t}>
                {/* Upper wick */}
                <line x1={x} y1={py(p.h)} x2={x} y2={bodyTop} stroke={color} strokeWidth={1} />
                {/* Lower wick */}
                <line x1={x} y1={bodyBot} x2={x} y2={py(p.l)} stroke={color} strokeWidth={1} />
                {/* Body */}
                <rect
                  x={x - candleW / 2}
                  y={bodyTop}
                  width={candleW}
                  height={bodyH}
                  fill={color}
                  opacity={0.9}
                />
              </g>
            )
          })}

          {/* Y-axis price labels */}
          {ticks.map((t, i) => (
            <text
              key={i}
              x={svgW - padR + 5}
              y={t.y + 3.5}
              fill="#71717a"
              fontSize={9}
              fontFamily="system-ui, sans-serif"
            >
              ${t.price.toFixed(0)}
            </text>
          ))}
        </>
      )}
    </svg>
  )
}

interface StockChartProps {
  symbol: string
}

export function StockChart({ symbol }: StockChartProps) {
  const [period, setPeriod] = useState("1m")
  const [chartType, setChartType] = useState<"area" | "candle">("area")
  const [mounted, setMounted] = useState(false)
  useEffect(() => { setMounted(true) }, [])

  const { data, isPending } = useQuery({
    queryKey: ["history", symbol, period],
    queryFn: () => getStockHistory(symbol, period),
    staleTime: 60_000,
  })

  const points = data?.data ?? []
  const isPositive =
    points.length >= 2 ? points[points.length - 1].c >= points[0].c : true
  const color = isPositive ? "#22c55e" : "#ef4444"
  const gradientId = `grad-${symbol}-${period}`

  return (
    <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-4">
      {/* Toolbar: period tabs left, chart type toggle right */}
      <div className="flex items-center justify-between mb-3">
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

        <div className="flex rounded-md border border-zinc-700 overflow-hidden text-xs">
          <button
            onClick={() => setChartType("area")}
            className={`px-3 py-1 transition-colors ${
              chartType === "area"
                ? "bg-zinc-700 text-white"
                : "text-zinc-400 hover:text-zinc-300 bg-transparent"
            }`}
          >
            Area
          </button>
          <button
            onClick={() => setChartType("candle")}
            className={`px-3 py-1 transition-colors border-l border-zinc-700 ${
              chartType === "candle"
                ? "bg-zinc-700 text-white"
                : "text-zinc-400 hover:text-zinc-300 bg-transparent"
            }`}
          >
            Candle
          </button>
        </div>
      </div>

      {/* Chart body — h-28 ≈ half of original h-56 */}
      {!mounted || isPending ? (
        <div className="h-28 w-full animate-pulse bg-zinc-800 rounded-lg" />
      ) : points.length === 0 ? (
        <div className="h-28 flex items-center justify-center text-zinc-500 text-sm">
          No chart data available
        </div>
      ) : chartType === "area" ? (
        <div className="h-28 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={points} margin={{ top: 2, right: 8, left: 0, bottom: 0 }}>
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
                minTickGap={50}
              />
              <YAxis
                domain={["auto", "auto"]}
                tick={{ fill: "#71717a", fontSize: 10 }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(v: number) => `$${v.toFixed(0)}`}
                width={46}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#18181b",
                  border: "1px solid #3f3f46",
                  borderRadius: "8px",
                  fontSize: "11px",
                }}
                labelStyle={{ color: "#a1a1aa" }}
                itemStyle={{ color: "#e4e4e7" }}
                labelFormatter={(v) => formatTooltipDate(v as number, period)}
                formatter={(v) => [`$${(v as number).toFixed(2)}`, "Price"]}
              />
              <Area
                type="monotone"
                dataKey="c"
                stroke={color}
                strokeWidth={1.5}
                fill={`url(#${gradientId})`}
                dot={false}
                activeDot={{ r: 3, strokeWidth: 0 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <div className="h-28 w-full">
          <CandlestickChart points={points} />
        </div>
      )}
    </div>
  )
}
