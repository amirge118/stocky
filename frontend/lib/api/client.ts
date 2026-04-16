import * as Sentry from "@sentry/nextjs"
import type { ApiErrorResponse } from "@/types"

/**
 * When empty, requests use same-origin paths like `/api/v1/...` so Next.js rewrites can proxy
 * to the backend (fixes production when the browser cannot reach localhost:8000).
 * Set `NEXT_PUBLIC_API_BASE_URL` to a full URL only if you need direct browser→API calls.
 */
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? ""

function reportError(error: {
  name: string
  status?: number
  code?: string
  message: string
  endpoint: string
}) {
  Sentry.captureException(new Error(error.message), {
    tags: { endpoint: error.endpoint, code: error.code ?? "unknown" },
    extra: { status: error.status },
  })
  // Fire-and-forget: never awaited, never throws
  fetch("/api/errors/log", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(error),
  }).catch(() => {
    /* silently ignore reporting failures */
  })
}

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
      const code = errorData.error?.code || (response.status === 503 ? "SERVICE_UNAVAILABLE" : "UNKNOWN_ERROR")
      const message =
        errorData.error?.message ||
        (errorData as unknown as { detail?: string }).detail ||
        (response.status === 503 ? "Service is warming up, please retry shortly" : "An error occurred")
      reportError({ name: "ApiError", status: response.status, code, message, endpoint })
      throw new ApiError(response.status, code, message, errorData.error?.details)
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
      const message =
        "Unable to connect to the server. Please check your internet connection and ensure the backend is running."
      reportError({ name: "NetworkError", message, endpoint })
      throw new NetworkError(message)
    }
    const message = error instanceof Error ? error.message : "Failed to connect to server"
    reportError({ name: "NetworkError", message, endpoint })
    throw new NetworkError(message)
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
