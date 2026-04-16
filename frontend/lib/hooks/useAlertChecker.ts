"use client"

import { useRef, useEffect } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { fetchAlerts, triggerAlert } from "@/lib/api/alerts"
import { ApiError } from "@/lib/api/client"
import { useStockPrices } from "./useStockPrices"

export function useAlertChecker() {
  const queryClient = useQueryClient()
  const notifiedRef = useRef<Set<number>>(new Set())

  useEffect(() => {
    if (typeof window !== "undefined" && "Notification" in window) {
      Notification.requestPermission()
    }
  }, [])

  const { data: alerts = [] } = useQuery({
    queryKey: ["alerts"],
    queryFn: () => fetchAlerts(50, 0),
    staleTime: 30_000,
    refetchInterval: 60_000,
    retry: (failureCount, error) => {
      if (error instanceof ApiError && error.status === 503) return failureCount < 5
      return failureCount < 2
    },
    retryDelay: (attempt) => Math.min(2000 * 2 ** attempt, 30_000),
    throwOnError: false,
  })

  const activeAlerts = alerts.filter((a) => a.is_active)
  const tickers = [...new Set(activeAlerts.map((a) => a.ticker))]

  // Always call hook — pass empty array when no active alerts
  const prices = useStockPrices(tickers)

  useEffect(() => {
    const active = alerts.filter((a) => a.is_active)
    for (const alert of active) {
      if (notifiedRef.current.has(alert.id)) continue

      const priceUpdate = prices[alert.ticker]
      if (!priceUpdate) continue

      const currentPrice = priceUpdate.price
      const targetPrice = parseFloat(alert.target_price)

      let triggered = false
      if (alert.condition_type === "ABOVE" && currentPrice > targetPrice) {
        triggered = true
      } else if (alert.condition_type === "BELOW" && currentPrice < targetPrice) {
        triggered = true
      } else if (
        alert.condition_type === "EQUAL" &&
        Math.abs(currentPrice - targetPrice) < 0.01
      ) {
        triggered = true
      }

      if (!triggered) continue

      notifiedRef.current.add(alert.id)

      if (
        typeof window !== "undefined" &&
        "Notification" in window &&
        Notification.permission === "granted"
      ) {
        new Notification(`${alert.ticker} Alert Triggered`, {
          body: `${alert.ticker} is ${alert.condition_type.toLowerCase()} $${targetPrice.toFixed(2)} — now at $${currentPrice.toFixed(2)}`,
          icon: "/favicon.ico",
        })
      }

      triggerAlert(alert.id, currentPrice).then(() => {
        queryClient.invalidateQueries({ queryKey: ["alerts"] })
      })
    }
  }, [prices, alerts, queryClient])
}
