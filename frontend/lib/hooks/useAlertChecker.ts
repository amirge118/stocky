"use client"

import { useEffect, useRef } from "react"
import { fetchStockData } from "@/lib/api/stocks"
import { useAlerts } from "./useAlerts"
import { useToast } from "@/hooks/use-toast"

const CHECK_INTERVAL_MS = 60_000 // 1 minute

export function useAlertChecker() {
  const { alerts, removeAlert } = useAlerts()
  const { toast } = useToast()
  const triggeredRef = useRef<Set<string>>(new Set())

  useEffect(() => {
    if (alerts.length === 0) return

    const checkAlerts = async () => {
      const symbolsToCheck = [...new Set(alerts.map((a) => a.symbol.toUpperCase()))]

      for (const sym of symbolsToCheck) {
        try {
          const data = await fetchStockData(sym)
          const price = data.current_price

          const relevantAlerts = alerts.filter((a) => a.symbol.toUpperCase() === sym)
          for (const alert of relevantAlerts) {
            const triggerKey = `${alert.id}-${alert.targetPrice}`
            const alreadyTriggered = triggeredRef.current.has(triggerKey)

            const crossed =
              alert.direction === "above"
                ? price >= alert.targetPrice
                : price <= alert.targetPrice

            if (crossed && !alreadyTriggered) {
              triggeredRef.current.add(triggerKey)
              toast({
                title: "Price Alert",
                description: `${alert.symbol} is now $${price.toFixed(2)} (${alert.direction} $${alert.targetPrice.toFixed(2)})`,
              })
              removeAlert(alert.id)
            }
          }
        } catch {
          // ignore fetch errors for individual symbols
        }
      }
    }

    const interval = setInterval(checkAlerts, CHECK_INTERVAL_MS)
    checkAlerts()

    return () => clearInterval(interval)
  }, [alerts, removeAlert, toast])
}
