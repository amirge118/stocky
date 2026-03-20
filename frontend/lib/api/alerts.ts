import type { Alert, AlertCreate, AlertUpdate } from "@/types/alerts"
import { del, get, patch, post } from "./client"

export function fetchAlerts(limit = 50, offset = 0, ticker?: string): Promise<Alert[]> {
  const url = `/api/v1/alerts?limit=${limit}&offset=${offset}${ticker ? `&ticker=${encodeURIComponent(ticker)}` : ""}`
  return get<Alert[]>(url)
}

export function createAlert(data: AlertCreate): Promise<Alert> {
  return post<Alert>("/api/v1/alerts", data)
}

export function updateAlert(id: number, data: AlertUpdate): Promise<Alert> {
  return patch<Alert>(`/api/v1/alerts/${id}`, data)
}

export function deleteAlert(id: number): Promise<void> {
  return del<void>(`/api/v1/alerts/${id}`)
}

export function triggerAlert(id: number, currentPrice: number): Promise<Alert> {
  return post<Alert>(`/api/v1/alerts/${id}/trigger`, { current_price: currentPrice })
}
