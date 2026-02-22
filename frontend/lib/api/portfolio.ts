import { get, post, del } from "./client"
import type { AddHoldingRequest, PortfolioPosition, PortfolioSummary } from "@/types/portfolio"

export async function getPortfolio(): Promise<PortfolioSummary> {
  return get<PortfolioSummary>("/api/v1/portfolio")
}

export async function addHolding(data: AddHoldingRequest): Promise<PortfolioPosition> {
  return post<PortfolioPosition>("/api/v1/portfolio", data)
}

export async function removeHolding(symbol: string): Promise<void> {
  await del(`/api/v1/portfolio/${symbol}`)
}
