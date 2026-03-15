import { get, post, del } from "./client"
import type {
  AddHoldingRequest,
  PortfolioHistoryResponse,
  PortfolioNewsItem,
  PortfolioPosition,
  PortfolioSummary,
  PortfolioSummaryWithSector,
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

export async function getPortfolioHistory(
  period = "1m"
): Promise<PortfolioHistoryResponse> {
  return get<PortfolioHistoryResponse>(`/api/v1/portfolio/history?period=${period}`)
}

export async function addHolding(data: AddHoldingRequest): Promise<PortfolioPosition> {
  return post<PortfolioPosition>("/api/v1/portfolio", data)
}

export async function removeHolding(symbol: string): Promise<void> {
  await del(`/api/v1/portfolio/${symbol}`)
}
