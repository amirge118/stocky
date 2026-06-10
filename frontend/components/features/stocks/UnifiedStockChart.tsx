"use client"

import { useState, useEffect } from "react"
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  Cell,
} from "recharts"
import { useUnifiedChartData } from "@/lib/hooks/useUnifiedChartData"
import type { UnifiedDataPoint } from "@/lib/hooks/useUnifiedChartData"

// ─── Constants ────────────────────────────────────────────────────────────────

const PERIODS = [
  { label: "1D", value: "1d" },
  { label: "1W", value: "1w" },
  { label: "1M", value: "1m" },
  { label: "6M", value: "6m" },
  { label: "1Y", value: "1y" },
  { label: "2Y", value: "2y" },
  { label: "5Y", value: "5y" },
]

const INDICATOR_TOGGLES = [
  { key: "bollinger" as const, label: "Bollinger", color: "#6366f1", requiresIndicators: true },
  { key: "rsi"       as const, label: "RSI",       color: "#f97316", requiresIndicators: true },
  { key: "macd"      as const, label: "MACD",      color: "#3b82f6", requiresIndicators: true },
  { key: "volume"    as const, label: "Volume",    color: "#71717a", requiresIndicators: false },
  { key: "sma20"     as const, label: "SMA 20",    color: "#f59e0b", requiresIndicators: true },
  { key: "sma50"     as const, label: "SMA 50",    color: "#60a5fa", requiresIndicators: true },
] as const

type ShowState = {
  bollinger: boolean; rsi: boolean; macd: boolean
  volume: boolean; sma20: boolean; sma50: boolean
}

const Y_AXIS_W = 46
const SUB_H    = 140
const SYNC_ID  = "stock-chart"

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatXAxis(ts: number, period: string): string {
  const d = new Date(ts)
  if (period === "1d") return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
  return d.toLocaleDateString([], { month: "short", day: "numeric" })
}

function formatTooltipDate(ts: number, period: string): string {
  const d = new Date(ts)
  if (period === "1d")
    return d.toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })
  return d.toLocaleDateString([], { month: "short", day: "numeric", year: "numeric" })
}

// ─── Candlestick via <Bar shape> (no scale access needed — uses pixel coords) ──

function CandleBarShape(props: any) {
  const { x, y, width, height, payload } = props
  if (!payload || payload.close == null) return null

  const open  = payload.open  ?? payload.close
  const close = payload.close
  const high  = payload.high  ?? Math.max(open, close)
  const low   = payload.low   ?? Math.min(open, close)

  const bullish  = close >= open
  const color    = bullish ? "#4ade80" : "#f87171"
  const cx       = x + width / 2
  const bodyRange = Math.max(open, close) - Math.min(open, close)
  const bodyH    = Math.max(1, height)

  // Extend wick beyond the body using the same px/unit ratio as the body
  let wickTopY    = y
  let wickBottomY = y + bodyH
  if (bodyRange > 0 && height > 0) {
    const pxPerUnit = height / bodyRange
    wickTopY    = y - (high  - Math.max(open, close)) * pxPerUnit
    wickBottomY = y + bodyH + (Math.min(open, close) - low) * pxPerUnit
  }

  const cw = Math.max(2, width * 0.7)
  return (
    <g>
      <line x1={cx} y1={wickTopY}    x2={cx} y2={y}          stroke={color} strokeWidth={1} />
      <line x1={cx} y1={y + bodyH}   x2={cx} y2={wickBottomY} stroke={color} strokeWidth={1} />
      <rect x={cx - cw / 2} y={y} width={cw} height={bodyH}  fill={color} opacity={0.9} />
    </g>
  )
}

// ─── Shared Row helper ────────────────────────────────────────────────────────

function Row({
  label, value, bold, labelColor, valueClass = "",
}: {
  label: string; value: string; bold?: boolean; labelColor?: string; valueClass?: string
}) {
  return (
    <div className="flex justify-between gap-3">
      <span style={labelColor ? { color: labelColor } : undefined} className={labelColor ? "" : "text-zinc-500"}>
        {label}
      </span>
      <span className={`font-mono tabular-nums ${bold ? "text-zinc-100" : "text-zinc-300"} ${valueClass}`}>
        {value}
      </span>
    </div>
  )
}

// ─── Tooltips ─────────────────────────────────────────────────────────────────

function PriceTooltip({ active, payload, label, show, hasIndicators, currency, period }: {
  active?: boolean
  payload?: Array<{ payload: UnifiedDataPoint }>
  label?: number
  show: ShowState
  hasIndicators: boolean
  currency: string
  period: string
}) {
  if (!active || !payload?.length || label == null) return null
  const dp = payload[0]?.payload
  if (!dp) return null
  const curr = currency === "ILS" ? "₪" : "$"
  const fmtP = (v: number | null) => (v != null ? `${curr}${v.toFixed(2)}` : "—")

  return (
    <div className="bg-zinc-900 border border-zinc-700 rounded-lg p-2.5 text-xs shadow-xl min-w-[160px] max-w-[200px]">
      <div className="text-zinc-400 mb-1.5 font-medium">{formatTooltipDate(label, period)}</div>
      <div className="space-y-0.5">
        <Row label="Close" value={fmtP(dp.close)} bold />
        {dp.open != null && (
          <>
            <Row label="Open"  value={fmtP(dp.open)} />
            <Row label="High"  value={fmtP(dp.high)}  valueClass="text-green-400" />
            <Row label="Low"   value={fmtP(dp.low)}   valueClass="text-red-400" />
          </>
        )}
        {show.volume && dp.volume != null && (
          <div className="pt-0.5 mt-0.5 border-t border-zinc-800">
            <Row label="Volume" value={dp.volume.toLocaleString()} valueClass="text-zinc-300" />
          </div>
        )}
      </div>
      {hasIndicators && (show.bollinger || show.sma20 || show.sma50) && (
        <div className="mt-1.5 pt-1.5 border-t border-zinc-800 space-y-0.5">
          {show.bollinger && (
            <>
              {dp.bbUpper  != null && <Row label="BB Upper" value={fmtP(dp.bbUpper)}  labelColor="#6366f1" />}
              {dp.bbMiddle != null && <Row label="BB Mid"   value={fmtP(dp.bbMiddle)} labelColor="#6366f1" />}
              {dp.bbLower  != null && <Row label="BB Lower" value={fmtP(dp.bbLower)}  labelColor="#6366f1" />}
            </>
          )}
          {show.sma20 && dp.sma20 != null && <Row label="SMA 20" value={fmtP(dp.sma20)} labelColor="#f59e0b" />}
          {show.sma50 && dp.sma50 != null && <Row label="SMA 50" value={fmtP(dp.sma50)} labelColor="#60a5fa" />}
        </div>
      )}
    </div>
  )
}

function RsiTooltip({ active, payload, label, period }: any) {
  if (!active || !payload?.length || label == null) return null
  const dp = payload[0]?.payload as UnifiedDataPoint
  if (dp?.rsi == null) return null
  return (
    <div className="bg-zinc-900 border border-zinc-700 rounded-lg p-2 text-xs shadow-xl">
      <div className="text-zinc-400 mb-1">{formatTooltipDate(label, period)}</div>
      <Row
        label="RSI (14)"
        value={`${dp.rsi.toFixed(2)}${dp.rsi > 70 ? " OB" : dp.rsi < 30 ? " OS" : ""}`}
        labelColor="#f97316"
        valueClass={dp.rsi > 70 ? "text-red-400" : dp.rsi < 30 ? "text-green-400" : ""}
      />
    </div>
  )
}

function MacdTooltip({ active, payload, label, period }: any) {
  if (!active || !payload?.length || label == null) return null
  const dp = payload[0]?.payload as UnifiedDataPoint
  if (dp?.macd == null) return null
  const fN = (v: number | null) => (v != null ? v.toFixed(4) : "—")
  return (
    <div className="bg-zinc-900 border border-zinc-700 rounded-lg p-2 text-xs shadow-xl">
      <div className="text-zinc-400 mb-1">{formatTooltipDate(label, period)}</div>
      <Row label="MACD"   value={fN(dp.macd)}       labelColor="#3b82f6" />
      {dp.macdSignal != null && <Row label="Signal" value={fN(dp.macdSignal)} labelColor="#f97316" />}
    </div>
  )
}

// ─── Main Component ───────────────────────────────────────────────────────────

interface UnifiedStockChartProps {
  symbol: string
  currency?: string
}

export function UnifiedStockChart({ symbol, currency = "USD" }: UnifiedStockChartProps) {
  const [period,    setPeriod]    = useState("1m")
  const [chartType, setChartType] = useState<"area" | "candle">("area")
  const [show,      setShow]      = useState<ShowState>({
    bollinger: true, rsi: true, macd: true, volume: true, sma20: true, sma50: true,
  })
  const [mounted, setMounted] = useState(false)
  useEffect(() => { setMounted(true) }, [])

  const { data, maxVolume, isPending, hasIndicators } = useUnifiedChartData(symbol, period)

  const currSymbol  = currency === "ILS" ? "₪" : "$"
  const isPositive  = data.length >= 2 ? data[data.length - 1].close >= data[0].close : true
  const priceColor  = isPositive ? "#4ade80" : "#f87171"
  const gradId      = `ucg-${symbol}`
  const bbGradId    = `ucbb-${symbol}`

  const toggle = (key: keyof ShowState) =>
    setShow((prev) => ({ ...prev, [key]: !prev[key] }))

  const showRsi      = show.rsi  && hasIndicators
  const showMacd     = show.macd && hasIndicators
  const subCount     = (showRsi ? 1 : 0) + (showMacd ? 1 : 0)
  const mainH        = subCount === 0 ? 480 : subCount === 1 ? 320 : 250
  const BASE_MARGIN  = { top: 8, right: 8, left: 0 }

  return (
    <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-4">

      {/* ── Controls ── */}
      <div className="flex flex-col gap-2.5 mb-3">
        {/* Period + chart-type row */}
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex gap-1 flex-wrap">
            {PERIODS.map((p) => (
              <button
                key={p.value}
                onClick={() => setPeriod(p.value)}
                className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                  period === p.value ? "bg-zinc-700 text-white" : "text-zinc-400 hover:text-zinc-200"
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

        {/* Indicator toggles */}
        <div className="flex flex-wrap gap-1.5">
          {INDICATOR_TOGGLES.map((t) => {
            const active   = show[t.key] && (hasIndicators || !t.requiresIndicators)
            const disabled = t.requiresIndicators && !hasIndicators
            return (
              <button
                key={t.key}
                onClick={() => toggle(t.key)}
                disabled={disabled}
                title={disabled ? "Not available for 1D / 1W / 2Y / 5Y" : undefined}
                style={
                  active
                    ? { borderColor: `${t.color}55`, backgroundColor: `${t.color}18`, color: t.color }
                    : undefined
                }
                className={`flex items-center gap-1 px-2 py-0.5 rounded border text-xs transition-colors ${
                  active ? "" : "border-zinc-700 text-zinc-500 bg-transparent"
                } disabled:opacity-40 disabled:cursor-not-allowed`}
              >
                <span
                  className="inline-block w-1.5 h-1.5 rounded-full shrink-0"
                  style={{ backgroundColor: t.color }}
                />
                {t.label}
              </button>
            )
          })}
        </div>
      </div>

      {/* ── Chart body ── */}
      {!mounted || isPending ? (
        <div className="h-[520px] w-full animate-pulse bg-zinc-800 rounded-lg" />
      ) : data.length === 0 ? (
        <div className="h-[520px] flex items-center justify-center text-zinc-500 text-sm">
          No chart data available
        </div>
      ) : (
        <div className="flex flex-col">

          {/* ── Price chart ── */}
          <div style={{ height: mainH }}>
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart
                data={data}
                margin={{ ...BASE_MARGIN, bottom: subCount === 0 ? 20 : 4 }}
                syncId={SYNC_ID}
              >
                <defs>
                  <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor={priceColor} stopOpacity={0.25} />
                    <stop offset="95%" stopColor={priceColor} stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id={bbGradId} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#6366f1" stopOpacity={0.1} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0.02} />
                  </linearGradient>
                </defs>

                <XAxis
                  dataKey="t"
                  tickFormatter={(v: number) => formatXAxis(v, period)}
                  tick={{ fill: "#71717a", fontSize: 10 }}
                  axisLine={false}
                  tickLine={false}
                  minTickGap={50}
                  hide={subCount > 0}
                />

                {/* Price Y-axis */}
                <YAxis
                  yAxisId="price"
                  orientation="left"
                  domain={["auto", "auto"]}
                  tick={{ fill: "#71717a", fontSize: 10 }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(v: number) => `${currSymbol}${v.toFixed(0)}`}
                  width={Y_AXIS_W}
                />

                {/* Volume scale (hidden, bottom ~15%) */}
                <YAxis
                  yAxisId="volume"
                  orientation="right"
                  domain={[0, maxVolume * 6.5]}
                  hide
                  width={0}
                />

                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />

                <Tooltip
                  content={
                    <PriceTooltip
                      show={show}
                      hasIndicators={hasIndicators}
                      currency={currency}
                      period={period}
                    />
                  }
                />

                {/* ── Area price ── */}
                {chartType === "area" && (
                  <Area
                    yAxisId="price"
                    type="monotone"
                    dataKey="close"
                    stroke={priceColor}
                    strokeWidth={1.5}
                    fill={`url(#${gradId})`}
                    dot={false}
                    activeDot={{ r: 3, strokeWidth: 0 }}
                    name="Price"
                  />
                )}

                {/* ── Candle: ghost Lines set Y-domain; Bar renders body+wick ── */}
                {chartType === "candle" && (
                  <>
                    <Line yAxisId="price" dataKey="high" strokeOpacity={0} dot={false} legendType="none" />
                    <Line yAxisId="price" dataKey="low"  strokeOpacity={0} dot={false} legendType="none" />
                    <Bar
                      yAxisId="price"
                      dataKey={(d: UnifiedDataPoint) =>
                        d.open != null
                          ? [Math.min(d.open, d.close), Math.max(d.open, d.close)]
                          : [d.close, d.close]
                      }
                      shape={<CandleBarShape />}
                      isAnimationActive={false}
                      legendType="none"
                    />
                  </>
                )}

                {/* ── Bollinger Bands ── */}
                {show.bollinger && hasIndicators && (
                  <>
                    <Area
                      yAxisId="price"
                      type="monotone"
                      dataKey="bbUpper"
                      stroke="#6366f1"
                      strokeWidth={1}
                      strokeDasharray="4 2"
                      fill={`url(#${bbGradId})`}
                      dot={false}
                      activeDot={false}
                      name="BB Upper"
                      legendType="none"
                    />
                    <Area
                      yAxisId="price"
                      type="monotone"
                      dataKey="bbLower"
                      stroke="#6366f1"
                      strokeWidth={1}
                      strokeDasharray="4 2"
                      fill="#18181b"
                      dot={false}
                      activeDot={false}
                      name="BB Lower"
                      legendType="none"
                    />
                    <Line
                      yAxisId="price"
                      type="monotone"
                      dataKey="bbMiddle"
                      stroke="#6366f1"
                      strokeWidth={1}
                      dot={false}
                      name="BB Mid"
                      legendType="none"
                    />
                  </>
                )}

                {/* ── SMA 20 ── */}
                {show.sma20 && hasIndicators && (
                  <Line
                    yAxisId="price"
                    type="monotone"
                    dataKey="sma20"
                    stroke="#f59e0b"
                    strokeWidth={1.5}
                    dot={false}
                    name="SMA 20"
                    legendType="none"
                  />
                )}

                {/* ── SMA 50 ── */}
                {show.sma50 && hasIndicators && (
                  <Line
                    yAxisId="price"
                    type="monotone"
                    dataKey="sma50"
                    stroke="#60a5fa"
                    strokeWidth={1.5}
                    dot={false}
                    name="SMA 50"
                    legendType="none"
                  />
                )}

                {/* ── Volume ── */}
                {show.volume && (
                  <Bar
                    yAxisId="volume"
                    dataKey="volume"
                    fill="#71717a"
                    opacity={0.35}
                    isAnimationActive={false}
                    name="Volume"
                    legendType="none"
                  />
                )}
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          {/* ── RSI sub-panel ── */}
          {showRsi && (
            <div className="relative border-t border-zinc-800 mt-0.5">
              <span className="absolute z-10 pointer-events-none select-none text-[10px] text-zinc-500"
                    style={{ left: Y_AXIS_W + 4, top: 4 }}>
                RSI (14)
              </span>
              <div style={{ height: SUB_H }}>
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart
                    data={data}
                    margin={{ ...BASE_MARGIN, bottom: showMacd ? 4 : 20 }}
                    syncId={SYNC_ID}
                  >
                    <XAxis
                      dataKey="t"
                      tickFormatter={(v: number) => formatXAxis(v, period)}
                      tick={{ fill: "#71717a", fontSize: 10 }}
                      axisLine={false}
                      tickLine={false}
                      minTickGap={50}
                      hide={showMacd}
                    />
                    <YAxis
                      domain={[0, 100]}
                      ticks={[30, 70]}
                      orientation="left"
                      tick={{ fill: "#71717a", fontSize: 9 }}
                      axisLine={false}
                      tickLine={false}
                      width={Y_AXIS_W}
                      tickFormatter={(v: number) => `${v}`}
                    />
                    <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                    <Tooltip content={<RsiTooltip period={period} />} />
                    <ReferenceLine y={70} stroke="#ef4444" strokeDasharray="3 3" strokeOpacity={0.5} />
                    <ReferenceLine y={30} stroke="#22c55e" strokeDasharray="3 3" strokeOpacity={0.5} />
                    <Line
                      type="monotone"
                      dataKey="rsi"
                      stroke="#f97316"
                      strokeWidth={1.5}
                      dot={false}
                      name="RSI"
                      legendType="none"
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* ── MACD sub-panel ── */}
          {showMacd && (
            <div className="relative border-t border-zinc-800 mt-0.5">
              <span className="absolute z-10 pointer-events-none select-none text-[10px] text-zinc-500"
                    style={{ left: Y_AXIS_W + 4, top: 4 }}>
                MACD (12,26,9)
              </span>
              <div style={{ height: SUB_H }}>
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart
                    data={data}
                    margin={{ ...BASE_MARGIN, bottom: 20 }}
                    syncId={SYNC_ID}
                  >
                    <XAxis
                      dataKey="t"
                      tickFormatter={(v: number) => formatXAxis(v, period)}
                      tick={{ fill: "#71717a", fontSize: 10 }}
                      axisLine={false}
                      tickLine={false}
                      minTickGap={50}
                    />
                    <YAxis
                      orientation="left"
                      tick={{ fill: "#71717a", fontSize: 9 }}
                      axisLine={false}
                      tickLine={false}
                      width={Y_AXIS_W}
                      tickFormatter={(v: number) => v.toFixed(1)}
                    />
                    <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                    <Tooltip content={<MacdTooltip period={period} />} />
                    <ReferenceLine y={0} stroke="#71717a" strokeOpacity={0.4} />
                    <Bar
                      dataKey="macdHist"
                      radius={[1, 1, 0, 0]}
                      isAnimationActive={false}
                      name="MACD Hist"
                      legendType="none"
                    >
                      {data.map((entry, i) => (
                        <Cell
                          key={`mh-${i}`}
                          fill={(entry.macdHist ?? 0) >= 0 ? "#4ade80" : "#f87171"}
                          fillOpacity={0.8}
                        />
                      ))}
                    </Bar>
                    <Line
                      type="monotone"
                      dataKey="macd"
                      stroke="#3b82f6"
                      strokeWidth={1.5}
                      dot={false}
                      name="MACD"
                      legendType="none"
                    />
                    <Line
                      type="monotone"
                      dataKey="macdSignal"
                      stroke="#f97316"
                      strokeWidth={1.5}
                      dot={false}
                      name="Signal"
                      legendType="none"
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

        </div>
      )}
    </div>
  )
}
