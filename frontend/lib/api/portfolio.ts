import { get, post, del } from "./client"
import type {
  AddHoldingRequest,
  PortfolioNewsItem,
  PortfolioPosition,
  PortfolioSummary,
  PortfolioSummaryWithSector,
  SellHoldingRequest,
  Transaction,
} from "@/types/portfolio"

export async function getPortfolio(): Promise<PortfolioSummary> {
  return get<PortfolioSummary>("/api/v1/portfolio")
}

export async function getPortfolioSummary(): Promise<PortfolioSummaryWithSector> {
  return get<PortfolioSummaryWithSector>("/api/v1/portfolio/summary")
}

export async function getPortfolioNews(limit = 20): Promise<PortfolioNewsItem[]> {
  return get<PortfolioNewsItem[]>(`/api/v1/portfolio/news?limit=${limit}`)
}

export async function addHolding(data: AddHoldingRequest): Promise<PortfolioPosition> {
  return post<PortfolioPosition>("/api/v1/portfolio", data)
}

export async function removeHolding(symbol: string): Promise<void> {
  await del(`/api/v1/portfolio/${symbol}`)
}

export async function sellHolding(
  symbol: string,
  data: SellHoldingRequest
): Promise<PortfolioPosition | null> {
  const result = await post<PortfolioPosition | undefined>(
    `/api/v1/portfolio/${symbol}/sell`,
    data
  )
  return result ?? null
}

export async function getTransactions(symbol?: string): Promise<Transaction[]> {
  const url = symbol
    ? `/api/v1/portfolio/transactions?symbol=${encodeURIComponent(symbol)}`
    : `/api/v1/portfolio/transactions`
  return get<Transaction[]>(url)
}
