import { get } from "./client"
import type { ApiResponse } from "@/types"

export interface HealthResponse {
  status: string
  timestamp: string
  version: string
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await get<ApiResponse<HealthResponse>>("/api/v1/health")
  return response.data
}
