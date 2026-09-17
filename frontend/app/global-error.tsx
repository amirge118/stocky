"use client"

import * as Sentry from "@sentry/nextjs"
import { useEffect } from "react"

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    Sentry.captureException(error)
  }, [error])

  return (
    <html>
      <body className="flex min-h-screen items-center justify-center bg-zinc-950 text-white">
        <div className="text-center">
          <h2 className="mb-4 text-xl font-bold">Something went wrong</h2>
          <button
            onClick={reset}
            className="rounded-lg bg-zinc-800 px-4 py-2 transition-colors hover:bg-zinc-700"
          >
            Try again
          </button>
        </div>
      </body>
    </html>
  )
}
