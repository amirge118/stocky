"use client"

import { useEffect, useRef, useState, useCallback } from "react"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"
const WS_BASE = API_BASE.replace(/^http/, "ws")

export interface PriceUpdate {
  symbol: string
  price: number
  change: number
  change_percent: number
}

export function useStockPrices(symbols: string[]) {
  const [prices, setPrices] = useState<Record<string, PriceUpdate>>({})
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)
  const symbolsKey = symbols.join(",")

  const connect = useCallback(() => {
    const syms = symbolsKey.split(",").filter(Boolean)
    if (syms.length === 0) return

    const url = `${WS_BASE}/api/v1/ws/prices`
    const ws = new WebSocket(url)

    ws.onopen = () => {
      ws.send(JSON.stringify({ subscribe: syms }))
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === "price" && data.symbol) {
          setPrices((prev) => ({
            ...prev,
            [data.symbol]: {
              symbol: data.symbol,
              price: data.price,
              change: data.change,
              change_percent: data.change_percent,
            },
          }))
        }
      } catch {
        // ignore parse errors
      }
    }

    ws.onclose = () => {
      wsRef.current = null
      reconnectTimeoutRef.current = setTimeout(connect, 5000)
    }

    ws.onerror = () => {
      ws.close()
    }

    wsRef.current = ws
  }, [symbolsKey])

  useEffect(() => {
    connect()
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [connect])

  return prices
}
