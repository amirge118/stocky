import { get, post, put, del } from "./client"
import type {
  Stock,
  StockAIAnalysis,
  StockCreate,
  StockData,
  StockDividendsResponse,
  StockEnrichedData,
  StockHistoryResponse,
  StockIndicatorsResponse,
  StockInfoResponse,
  StockListResponse,
  StockNewsItem,
  StockSearchResult,
  StockUpdate,
} from "@/types/stock"

export interface GetStocksOptions {
  page?: number
  limit?: number
}

export async function getStocks(
  options?: GetStocksOptions
): Promise<StockListResponse> {
  const params = new URLSearchParams()
  if (options?.page) params.append("page", options.page.toString())
  if (options?.limit) params.append("limit", options.limit.toString())

  const query = params.toString()
  return get<StockListResponse>(`/api/v1/stocks${query ? `?${query}` : ""}`)
}

export async function getStock(symbol: string): Promise<Stock> {
  return get<Stock>(`/api/v1/stocks/${symbol}`)
}

export async function createStock(data: StockCreate): Promise<Stock> {
  return post<Stock>("/api/v1/stocks", data)
}

export async function updateStock(
  symbol: string,
  data: StockUpdate
): Promise<Stock> {
  return put<Stock>(`/api/v1/stocks/${symbol}`, data)
}

export async function deleteStock(symbol: string): Promise<void> {
  await del(`/api/v1/stocks/${symbol}`)
}

export async function fetchStockData(symbol: string): Promise<StockData> {
  return get<StockData>(`/api/v1/stocks/${symbol}/data`)
}

export async function fetchStockDataBatch(
  symbols: string[]
): Promise<Record<string, StockData>> {
  if (symbols.length === 0) return {}
  return post<Record<string, StockData>>("/api/v1/stocks/batch-data", {
    symbols: symbols.slice(0, 50),
  })
}

export async function searchStocks(query: string): Promise<StockSearchResult[]> {
  return get<StockSearchResult[]>(`/api/v1/stocks/search?q=${encodeURIComponent(query)}`)
}

export async function getStockHistory(symbol: string, period: string): Promise<StockHistoryResponse> {
  return get<StockHistoryResponse>(`/api/v1/stocks/${symbol}/history?period=${period}`)
}

export async function getStockInfo(symbol: string): Promise<StockInfoResponse> {
  return get<StockInfoResponse>(`/api/v1/stocks/${symbol}/info`)
}

export async function getStockNews(symbol: string): Promise<StockNewsItem[]> {
  return get<StockNewsItem[]>(`/api/v1/stocks/${symbol}/news`)
}

export async function getStockAnalysis(symbol: string): Promise<StockAIAnalysis> {
  return get<StockAIAnalysis>(`/api/v1/stocks/${symbol}/analysis`)
}

export async function getStockIndicators(symbol: string, period: string = "6m"): Promise<StockIndicatorsResponse> {
  return get<StockIndicatorsResponse>(`/api/v1/stocks/${symbol.toUpperCase()}/indicators?period=${period}`)
}

export async function getStockDividends(symbol: string, years: number = 5): Promise<StockDividendsResponse> {
  return get<StockDividendsResponse>(`/api/v1/stocks/${symbol.toUpperCase()}/dividends?years=${years}`)
}

export async function fetchStockEnrichedBatch(
  symbols: string[]
): Promise<Record<string, StockEnrichedData>> {
  if (symbols.length === 0) return {}
  return post<Record<string, StockEnrichedData>>("/api/v1/stocks/enriched-batch", {
    symbols: symbols.slice(0, 50),
  })
}

export interface SectorPeer {
  symbol: string
  name: string
  sector: string | null
  industry: string | null
  current_price: number | null
  day_change_percent: number | null
  pe_ratio: number | null
  market_cap: number | null
  is_current: boolean
}

export async function getSectorPeers(
  sector: string,
  symbol?: string,
  limit = 10
): Promise<SectorPeer[]> {
  const params = new URLSearchParams({ sector })
  if (symbol) params.append("symbol", symbol)
  params.append("limit", limit.toString())
  return get<SectorPeer[]>(`/api/v1/stocks/sector-peers?${params}`)
}

export interface CompareSummary {
  symbols: string[]
  summary: string
}

export async function getCompareSummary(symbols: string[]): Promise<CompareSummary> {
  return get<CompareSummary>(
    `/api/v1/stocks/compare-summary?symbols=${symbols.join(",")}`
  )
}
