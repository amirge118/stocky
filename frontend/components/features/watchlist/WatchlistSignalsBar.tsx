"use client"

import { useMemo } from "react"
import { useQuery } from "@tanstack/react-query"
import { getWatchlistMomentumSignals } from "@/lib/api/watchlists"
import { ApiError } from "@/lib/api/client"
import type { WatchlistItem, WatchlistSignal } from "@/types/watchlist"
import type { StockData, StockEnrichedData } from "@/types/stock"

interface WatchlistSignalsBarProps {
  symbols: string[]
  listId: number | null
  batchPrices: Record<string, StockData>
  enrichedMap: Record<string, StockEnrichedData>
  changePctMap: Record<string, number>
  items: WatchlistItem[]
}

const PILL_STYLES: Record<string, string> = {
  volume_spike:
    "bg-amber-500/15 border border-amber-500/30 text-amber-300",
  momentum:
    "bg-amber-500/15 border border-amber-500/30 text-amber-300",
  breakout_high:
    "bg-blue-500/15 border border-blue-500/30 text-blue-300",
  breakout_low:
    "bg-rose-500/15 border border-rose-500/30 text-rose-300",
  sector_sweep:
    "bg-purple-500/15 border border-purple-500/30 text-purple-300",
}

const KIND_ICON: Record<string, string> = {
  volume_spike: "⚡",
  momentum: "~",
  breakout_high: "△",
  breakout_low: "▽",
  sector_sweep: "⬡",
}

export function WatchlistSignalsBar({
  symbols,
  listId,
  batchPrices,
  enrichedMap,
  changePctMap,
  items,
}: WatchlistSignalsBarProps) {
  // ── Frontend-computed signals ──────────────────────────────────────────────
  const frontendSignals = useMemo<WatchlistSignal[]>(() => {
    const signals: WatchlistSignal[] = []

    // Volume spike: current volume > 2× avg_volume
    const volSpikes: string[] = []
    for (const sym of symbols) {
      const vol = batchPrices[sym]?.volume
      const avgVol = enrichedMap[sym]?.avg_volume
      if (vol && avgVol && avgVol > 0 && vol / avgVol >= 2.0) {
        volSpikes.push(sym)
      }
    }
    if (volSpikes.length > 0) {
      const ratios = volSpikes.map((sym) => {
        const vol = batchPrices[sym]?.volume ?? 0
        const avg = enrichedMap[sym]?.avg_volume ?? 1
        return `${sym} ${(vol / avg).toFixed(1)}×`
      })
      signals.push({
        kind: "volume_spike",
        label: "Volume Spike",
        detail: ratios.slice(0, 3).join(", "),
        symbols: volSpikes,
        severity: volSpikes.length >= 3 ? "high" : "medium",
      })
    }

    // Price breakout: within 2% of 52W high or low
    const highBreaks: string[] = []
    const lowBreaks: string[] = []
    for (const sym of symbols) {
      const price = batchPrices[sym]?.current_price
      const high = enrichedMap[sym]?.fifty_two_week_high
      const low = enrichedMap[sym]?.fifty_two_week_low
      if (price && high && price >= high * 0.98) highBreaks.push(sym)
      if (price && low && price <= low * 1.02) lowBreaks.push(sym)
    }
    if (highBreaks.length > 0) {
      signals.push({
        kind: "breakout_high",
        label: "Near 52W High",
        detail: highBreaks.slice(0, 3).join(", "),
        symbols: highBreaks,
        severity: "medium",
      })
    }
    if (lowBreaks.length > 0) {
      signals.push({
        kind: "breakout_low",
        label: "Near 52W Low",
        detail: lowBreaks.slice(0, 3).join(", "),
        symbols: lowBreaks,
        severity: "medium",
      })
    }

    // Sector sweep: ≥60% of stocks in same sector moving >1% in same direction
    const bySector: Record<string, string[]> = {}
    for (const item of items) {
      if (!item.sector) continue
      if (!bySector[item.sector]) bySector[item.sector] = []
      bySector[item.sector].push(item.symbol)
    }
    for (const [sector, syms] of Object.entries(bySector)) {
      if (syms.length < 3) continue
      const ups = syms.filter((s) => (changePctMap[s] ?? 0) > 1.0).length
      const downs = syms.filter((s) => (changePctMap[s] ?? 0) < -1.0).length
      const dominant = ups >= downs ? ups : downs
      const direction = ups >= downs ? "up" : "down"
      if (dominant / syms.length >= 0.6) {
        signals.push({
          kind: "sector_sweep",
          label: "Sector Sweep",
          detail: `${sector} — ${dominant}/${syms.length} ${direction}`,
          symbols: syms,
          severity: dominant / syms.length >= 0.8 ? "high" : "medium",
        })
      }
    }

    return signals
  }, [symbols, batchPrices, enrichedMap, changePctMap, items])

  // ── Backend momentum signal ────────────────────────────────────────────────
  // Retry up to 5× on 503 (Render cold start) with exponential backoff.
  // This is a non-critical signal so errors are swallowed — the bar just
  // shows frontend-only signals until the backend wakes up.
  const { data: momentumData } = useQuery({
    queryKey: ["watchlistMomentum", listId, symbols.join(",")],
    queryFn: () => getWatchlistMomentumSignals(listId!, symbols),
    enabled: listId !== null && symbols.length > 0,
    staleTime: 5 * 60_000,
    retry: (failureCount, error) => {
      if (error instanceof ApiError && error.status === 503) {
        return failureCount < 5
      }
      return failureCount < 2
    },
    retryDelay: (attempt) => Math.min(2000 * 2 ** attempt, 30_000),
    throwOnError: false,
  })

  const momentumSignals = useMemo<WatchlistSignal[]>(() => {
    if (!momentumData?.signals?.length) return []
    return momentumData.signals.map((s) => ({
      kind: "momentum" as const,
      label: "Unusual Move",
      detail: `${s.symbol} ${s.last_return_pct >= 0 ? "+" : ""}${s.last_return_pct.toFixed(1)}% (Z ${s.z_score >= 0 ? "+" : ""}${s.z_score})`,
      symbols: [s.symbol],
      severity: Math.abs(s.z_score) >= 3 ? "high" : "medium",
    }))
  }, [momentumData])

  const allSignals = [...frontendSignals, ...momentumSignals]

  if (allSignals.length === 0) return null

  return (
    <div className="flex flex-wrap gap-1.5 mb-3">
      {allSignals.map((signal, idx) => (
        <div
          key={`${signal.kind}-${idx}`}
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${PILL_STYLES[signal.kind]}`}
          title={`Affected: ${signal.symbols.join(", ")}`}
        >
          <span>{KIND_ICON[signal.kind]}</span>
          <span className="font-semibold">{signal.label}</span>
          <span className="opacity-75">·</span>
          <span className="opacity-75">{signal.detail}</span>
        </div>
      ))}
    </div>
  )
}
