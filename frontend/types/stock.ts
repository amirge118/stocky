// Stock-related TypeScript types

export interface Stock {
  id: number
  symbol: string
  name: string
  exchange: string
  sector: string | null
  created_at: string
  updated_at: string | null
}

export interface StockCreate {
  symbol: string
  name: string
  exchange: string
  sector?: string | null
}

export interface StockUpdate {
  name?: string
  exchange?: string
  sector?: string | null
}

export interface StockData {
  symbol: string
  name: string
  current_price: number
  previous_close: number
  change: number
  change_percent: number
  volume: number | null
  market_cap: number | null
  currency: string
}

export interface StockSearchResult {
  symbol: string
  name: string
  exchange: string
  sector: string | null
  industry: string | null
  current_price: number | null
  currency: string | null
  country: string | null
  sparkline: number[] | null
}

export interface StockListResponse {
  data: Stock[]
  meta: {
    page: number
    limit: number
    total: number
    total_pages: number
  }
}

export interface StockHistoryPoint {
  t: number   // Unix ms
  o: number   // open
  h: number   // high
  l: number   // low
  c: number   // close
  v: number | null  // volume
}

export interface StockHistoryResponse {
  symbol: string
  period: string
  data: StockHistoryPoint[]
}

export interface StockInfoResponse {
  symbol: string
  description: string | null
  website: string | null
  employees: number | null
  ceo: string | null
  country: string | null
  sector: string | null
  industry: string | null
  market_cap: number | null
  pe_ratio: number | null
  forward_pe: number | null
  beta: number | null
  dividend_yield: number | null
  fifty_two_week_high: number | null
  fifty_two_week_low: number | null
  average_volume: number | null
}

export interface StockNewsItem {
  title: string
  publisher: string | null
  link: string | null
  published_at: number | null  // Unix ms
}

export interface StockAIAnalysis {
  symbol: string
  analysis: string
}

export interface DividendPoint { t: number; amount: number }
export interface StockDividendsResponse {
  symbol: string
  currency: string
  dividends: DividendPoint[]
  annual_yield: number | null
}

export interface IndicatorPoint { t: number; v: number | null }
export interface BollingerPoint { t: number; upper: number | null; middle: number | null; lower: number | null }
export interface MacdPoint { t: number; macd: number | null; signal: number | null; hist: number | null }
export interface StockIndicatorsResponse {
  symbol: string
  period: string
  sma20: IndicatorPoint[]
  sma50: IndicatorPoint[]
  rsi: IndicatorPoint[]
  macd: MacdPoint[]
  bollinger: BollingerPoint[]
}

export interface StockEnrichedData {
  symbol: string
  fifty_two_week_high: number | null
  fifty_two_week_low: number | null
  avg_volume: number | null
  analyst_rating: string | null  // "buy" | "hold" | "sell" | "strong_buy" | "underperform"
}
