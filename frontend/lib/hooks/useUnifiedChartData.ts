"use client"

import { useMemo } from "react"
import { useQuery } from "@tanstack/react-query"
import { getStockHistory, getStockIndicators } from "@/lib/api/stocks"
import type {
  StockHistoryResponse,
  StockIndicatorsResponse,
} from "@/types/stock"

export interface UnifiedDataPoint {
  t: number
  close: number
  open: number | null
  high: number | null
  low: number | null
  volume: number | null
  sma20: number | null
  sma50: number | null
  rsi: number | null
  macd: number | null
  macdSignal: number | null
  macdHist: number | null
  bbUpper: number | null
  bbMiddle: number | null
  bbLower: number | null
}

export const INDICATOR_PERIODS = ["1m", "6m", "1y"]

function findClosest<T extends { t: number }>(
  arr: T[],
  ts: number
): T | undefined {
  if (arr.length === 0) return undefined
  let lo = 0
  let hi = arr.length - 1
  while (lo < hi) {
    const mid = Math.floor((lo + hi) / 2)
    if (arr[mid].t < ts) lo = mid + 1
    else hi = mid
  }
  if (lo > 0 && Math.abs(arr[lo - 1].t - ts) < Math.abs(arr[lo].t - ts)) {
    return arr[lo - 1]
  }
  return arr[lo]
}

export function useUnifiedChartData(symbol: string, period: string) {
  const hasIndicators = INDICATOR_PERIODS.includes(period)

  const {
    data: histData,
    isPending: histPending,
    isError,
  } = useQuery<StockHistoryResponse>({
    queryKey: ["history", symbol, period],
    queryFn: () => getStockHistory(symbol, period),
    staleTime: 60_000,
  })

  const { data: indData, isPending: indPending } = useQuery<StockIndicatorsResponse>({
    queryKey: ["indicators", symbol, period],
    queryFn: () => getStockIndicators(symbol, period),
    staleTime: 5 * 60_000,
    enabled: hasIndicators,
  })

  const data = useMemo<UnifiedDataPoint[]>(() => {
    const points = histData?.data ?? []
    if (points.length === 0) return []

    return points.map((pt) => {
      const base: UnifiedDataPoint = {
        t: pt.t,
        close: pt.c,
        open: pt.o,
        high: pt.h,
        low: pt.l,
        volume: pt.v,
        sma20: null,
        sma50: null,
        rsi: null,
        macd: null,
        macdSignal: null,
        macdHist: null,
        bbUpper: null,
        bbMiddle: null,
        bbLower: null,
      }

      if (!indData) return base

      const rsiPt = findClosest(indData.rsi, pt.t)
      const sma20Pt = findClosest(indData.sma20, pt.t)
      const sma50Pt = findClosest(indData.sma50, pt.t)
      const macdPt = findClosest(indData.macd, pt.t)
      const bbPt = findClosest(indData.bollinger, pt.t)

      return {
        ...base,
        rsi: rsiPt?.v ?? null,
        sma20: sma20Pt?.v ?? null,
        sma50: sma50Pt?.v ?? null,
        macd: macdPt?.macd ?? null,
        macdSignal: macdPt?.signal ?? null,
        macdHist: macdPt?.hist ?? null,
        bbUpper: bbPt?.upper ?? null,
        bbMiddle: bbPt?.middle ?? null,
        bbLower: bbPt?.lower ?? null,
      }
    })
  }, [histData, indData])

  const maxVolume = useMemo(
    () => Math.max(1, ...data.map((d) => d.volume ?? 0)),
    [data]
  )

  return {
    data,
    maxVolume,
    isPending: histPending || (hasIndicators && indPending),
    isError,
    hasIndicators,
  }
}
