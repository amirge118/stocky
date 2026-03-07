export interface AgentMeta {
  name: string
  agent_type: "stock" | "portfolio" | "market" | "sector" | string
  description: string
  schedule_cron: string | null
}

export interface AgentListResponse {
  agents: AgentMeta[]
}

export interface AgentReport {
  id: number
  agent_name: string
  agent_type: string
  status: "pending" | "running" | "completed" | "failed"
  target_symbol: string | null
  data: Record<string, unknown> | null
  error_message: string | null
  tokens_used: number | null
  run_duration_ms: number | null
  created_at: string
  updated_at: string | null
}

export interface TriggerResponse {
  status: string
  agent_name: string
  target_symbol: string | null
  message: string
}

export interface SectorSlice {
  sector: string
  total_value: number
  weight_pct: number
  symbols: string[]
  num_holdings: number
}

export interface SectorBreakdown {
  sectors: SectorSlice[]
  total_value: number
}
