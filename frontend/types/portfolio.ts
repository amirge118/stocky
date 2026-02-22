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
}

export interface PortfolioSummary {
  positions: PortfolioPosition[]
  total_value: number
  total_cost: number
  total_gain_loss: number
  total_gain_loss_pct: number
}

export interface AddHoldingRequest {
  symbol: string
  name: string
  shares: number
  price_per_share: number
}
