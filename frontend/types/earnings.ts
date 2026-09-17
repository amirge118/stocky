export interface EarningsEvent {
  symbol: string
  earnings_date: string
  eps_estimate: number | null
  eps_actual: number | null
  surprise_pct: number | null
  revenue_estimate: number | null
  revenue_actual: number | null
  is_upcoming: boolean
  days_until: number | null
}

export interface EarningsCalendarResponse {
  items: EarningsEvent[]
}
