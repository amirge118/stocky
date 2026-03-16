import { get } from "./client"
import type { MarketOverviewResponse } from "@/types/market"

export async function getMarketOverview(): Promise<MarketOverviewResponse> {
  return get<MarketOverviewResponse>("/api/v1/market/overview")
}
