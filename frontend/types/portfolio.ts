export interface PortfolioPosition {
  symbol: string
  name: string
  shares: number
  avg_cost: number
  total_cost: number
  current_price: number | null
  current_value: number | null
  gain_loss: number | null
  gain_loss_pct: number | null
  portfolio_pct: number | null
  day_change: number | null
  day_change_percent: number | null
}

export interface PortfolioSummary {
  positions: PortfolioPosition[]
  total_value: number
  total_cost: number
  total_gain_loss: number
  total_gain_loss_pct: number
  total_day_change: number | null
  total_day_change_pct: number | null
}

import type { SectorBreakdown } from "./agent"

export interface PortfolioSummaryWithSector {
  portfolio: PortfolioSummary
  sector_breakdown: SectorBreakdown
}

export interface AddHoldingRequest {
  symbol: string
  name: string
  shares: number
  price_per_share: number
  purchase_date?: string
}

export interface PortfolioNewsItem {
  symbol: string
  title: string
  publisher: string | null
  link: string | null
  published_at: number | null
}

export interface PortfolioHistoryPoint {
  t: number
  value: number
}

export interface PortfolioHistoryResponse {
  period: string
  data: PortfolioHistoryPoint[]
}
