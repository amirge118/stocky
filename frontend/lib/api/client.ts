import type { ApiErrorResponse } from "@/types"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details?: Record<string, unknown>
  ) {
    super(message)
    this.name = "ApiError"
  }
}

export class NetworkError extends Error {
  constructor(message: string) {
    super(message)
    this.name = "NetworkError"
  }
}

export async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    })

    if (!response.ok) {
      const errorData = (await response.json().catch(() => ({}))) as ApiErrorResponse
      throw new ApiError(
        response.status,
        errorData.error?.code || "UNKNOWN_ERROR",
        errorData.error?.message || (errorData as unknown as { detail?: string }).detail || "An error occurred",
        errorData.error?.details
      )
    }

    if (response.status === 204 || response.headers.get("content-length") === "0") {
      return undefined as T
    }

    const data = await response.json()
    return data as T
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    // Network error or fetch failure
    if (error instanceof TypeError && error.message.includes("fetch")) {
      throw new NetworkError(
        "Unable to connect to the server. Please check your internet connection and ensure the backend is running."
      )
    }
    throw new NetworkError(
      error instanceof Error ? error.message : "Failed to connect to server"
    )
  }
}

export async function get<T>(endpoint: string): Promise<T> {
  return apiRequest<T>(endpoint, { method: "GET" })
}

export async function post<T>(endpoint: string, data?: unknown): Promise<T> {
  return apiRequest<T>(endpoint, {
    method: "POST",
    body: data ? JSON.stringify(data) : undefined,
  })
}

export async function put<T>(endpoint: string, data?: unknown): Promise<T> {
  return apiRequest<T>(endpoint, {
    method: "PUT",
    body: data ? JSON.stringify(data) : undefined,
  })
}

export async function patch<T>(endpoint: string, data?: unknown): Promise<T> {
  return apiRequest<T>(endpoint, {
    method: "PATCH",
    body: data ? JSON.stringify(data) : undefined,
  })
}

export async function del<T>(endpoint: string): Promise<T> {
  return apiRequest<T>(endpoint, { method: "DELETE" })
}
