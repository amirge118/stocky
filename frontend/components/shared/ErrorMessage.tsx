"use client"

import { ApiError, NetworkError } from "@/lib/api/client"

interface ErrorMessageProps {
  error: Error | ApiError | NetworkError
  onRetry?: () => void
}

function getUserFriendlyMessage(error: Error | ApiError | NetworkError): string {
  if (error instanceof NetworkError) {
    return error.message || "Unable to connect to server. Please check your connection."
  }
  if (error instanceof ApiError) {
    const errorMessages: Record<string, string> = {
      STOCK_NOT_FOUND: "The stock you are looking for was not found.",
      VALIDATION_ERROR: "Please check your input and try again.",
      NETWORK_ERROR: "Unable to connect to server. Please check your connection.",
      DUPLICATE_STOCK: "This stock already exists in your portfolio.",
    }
    return errorMessages[error.code] || error.message || "Something went wrong. Please try again."
  }
  return error.message || "An unexpected error occurred."
}

export function ErrorMessage({ error, onRetry }: ErrorMessageProps) {
  const message = getUserFriendlyMessage(error)

  return (
    <div className="rounded-lg border border-destructive bg-destructive/10 p-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-destructive">{message}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="ml-4 px-3 py-1 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          >
            Retry
          </button>
        )}
      </div>
    </div>
  )
}
