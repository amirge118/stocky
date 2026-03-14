"use client"

import { useState, useEffect, useCallback } from "react"

const ALERTS_STORAGE_KEY = "stock-price-alerts"

export interface PriceAlert {
  id: string
  symbol: string
  targetPrice: number
  direction: "above" | "below"
  createdAt: number
}

export function useAlerts() {
  const [alerts, setAlerts] = useState<PriceAlert[]>([])

  useEffect(() => {
    try {
      const stored = localStorage.getItem(ALERTS_STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored) as PriceAlert[]
        setAlerts(Array.isArray(parsed) ? parsed : [])
      }
    } catch (error) {
      console.error("Failed to load alerts from localStorage:", error)
      setAlerts([])
    }
  }, [])

  useEffect(() => {
    try {
      localStorage.setItem(ALERTS_STORAGE_KEY, JSON.stringify(alerts))
    } catch (error) {
      console.error("Failed to save alerts to localStorage:", error)
    }
  }, [alerts])

  const addAlert = useCallback((symbol: string, targetPrice: number, direction: "above" | "below") => {
    const id = `${symbol}-${targetPrice}-${direction}-${Date.now()}`
    const newAlert: PriceAlert = {
      id,
      symbol: symbol.toUpperCase(),
      targetPrice,
      direction,
      createdAt: Date.now(),
    }
    setAlerts((prev) => [...prev, newAlert])
    return id
  }, [])

  const removeAlert = useCallback((id: string) => {
    setAlerts((prev) => prev.filter((a) => a.id !== id))
  }, [])

  const getAlertsForSymbol = useCallback(
    (symbol: string) => {
      return alerts.filter((a) => a.symbol.toUpperCase() === symbol.toUpperCase())
    },
    [alerts]
  )

  const clearAlerts = useCallback(() => {
    setAlerts([])
  }, [])

  return {
    alerts,
    addAlert,
    removeAlert,
    getAlertsForSymbol,
    clearAlerts,
  }
}
