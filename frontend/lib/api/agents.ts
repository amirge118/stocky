import { get, post } from "./client"
import type {
  AgentListResponse,
  AgentReport,
  TriggerResponse,
  SectorBreakdown,
} from "@/types/agent"

export async function listAgents(): Promise<AgentListResponse> {
  return get<AgentListResponse>("/api/v1/agents")
}

export async function triggerAgent(
  name: string,
  params?: { symbol?: string; sector?: string }
): Promise<TriggerResponse> {
  const query = new URLSearchParams()
  if (params?.symbol) query.append("symbol", params.symbol)
  if (params?.sector) query.append("sector", params.sector)
  const qs = query.toString()
  return post<TriggerResponse>(
    `/api/v1/agents/${name}/trigger${qs ? `?${qs}` : ""}`,
  )
}

export async function getLatestReport(
  name: string,
  symbol?: string,
): Promise<AgentReport | null> {
  const query = symbol ? `?symbol=${encodeURIComponent(symbol)}` : ""
  return get<AgentReport | null>(`/api/v1/agents/${name}/latest${query}`)
}

export async function getAgentHistory(
  name: string,
  symbol?: string,
  limit = 20,
): Promise<AgentReport[]> {
  const query = new URLSearchParams({ limit: limit.toString() })
  if (symbol) query.append("symbol", symbol)
  return get<AgentReport[]>(`/api/v1/agents/${name}/history?${query}`)
}

export async function getSectorBreakdown(): Promise<SectorBreakdown> {
  return get<SectorBreakdown>("/api/v1/portfolio/sector-breakdown")
}
