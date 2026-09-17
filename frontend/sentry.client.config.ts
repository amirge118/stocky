import * as Sentry from "@sentry/nextjs"

const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN

if (dsn) {
  Sentry.init({
    dsn,
    // Capture 10% of transactions for performance monitoring
    tracesSampleRate: 0.1,
    environment: process.env.NODE_ENV,
    replaysSessionSampleRate: 0,
    replaysOnErrorSampleRate: 1.0,
    // Ignore common non-actionable errors
    ignoreErrors: [
      "ResizeObserver loop limit exceeded",
      "ResizeObserver loop completed with undelivered notifications",
      "Non-Error promise rejection captured",
    ],
  })
}
