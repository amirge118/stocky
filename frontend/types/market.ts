export interface IndexData {
  symbol: string
  name: string
  price: number
  change: number
  change_percent: number
  sparkline: number[]
}

export interface SectorNewsItem {
  title: string
  url: string | null
  publisher: string | null
}

export interface SectorData {
  name: string
  etf: string
  price: number
  change_percent: number
  news: SectorNewsItem[]
}

export interface MoverData {
  symbol: string
  name: string
  price: number
  change_percent: number
}

export interface MarketOverviewResponse {
  indices: IndexData[]
  sectors: SectorData[]
  gainers: MoverData[]
  losers: MoverData[]
  updated_at: string
}
