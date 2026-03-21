import * as Sentry from "@sentry/nextjs"

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  // Capture 10% of transactions for performance monitoring
  tracesSampleRate: 0.1,
  // Only enable in production
  enabled: process.env.NODE_ENV === "production",
  environment: process.env.NODE_ENV,
  // Ignore common non-actionable errors
  ignoreErrors: [
    "ResizeObserver loop limit exceeded",
    "ResizeObserver loop completed with undelivered notifications",
    "Non-Error promise rejection captured",
  ],
})
