// Common types used across the application

export interface ApiError {
  code: string
  message: string
  details?: Record<string, unknown>
}

export interface ApiResponse<T> {
  data: T
  meta?: {
    timestamp?: string
    version?: string
  }
}

export interface ApiErrorResponse {
  error: ApiError
}
