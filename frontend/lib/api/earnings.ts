import { get } from "./client"
import type { EarningsCalendarResponse } from "@/types/earnings"

export async function getStockEarnings(
  symbol: string
): Promise<EarningsCalendarResponse> {
  return get<EarningsCalendarResponse>(
    `/api/v1/stocks/${symbol.toUpperCase()}/earnings`
  )
}

export async function getEarningsCalendar(
  symbols: string[]
): Promise<EarningsCalendarResponse> {
  if (symbols.length === 0) return { items: [] }
  return get<EarningsCalendarResponse>(
    `/api/v1/earnings/calendar?symbols=${symbols.join(",")}`
  )
}
