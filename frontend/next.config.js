/** @type {import('next').NextConfig} */
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
})
const { withSentryConfig } = require('@sentry/nextjs')

const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  // unsafe-eval needed for Next.js dev HMR; tighten in prod
              "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
              "font-src 'self' https://fonts.gstatic.com",
              "img-src 'self' data: blob: https:",
              "connect-src 'self' ws://localhost:8000 wss://localhost:8000 http://localhost:8000 https:",
              "frame-ancestors 'none'",
            ].join('; '),
          },
          { key: 'X-DNS-Prefetch-Control', value: 'on' },
          { key: 'Strict-Transport-Security', value: 'max-age=63072000; includeSubDomains; preload' },
          { key: 'X-Frame-Options', value: 'SAMEORIGIN' },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'X-XSS-Protection', value: '1; mode=block' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
        ],
      },
    ]
  },
  // swcMinify is deprecated in Next.js 15 - minification is enabled by default
  images: {
    domains: [],
    formats: ['image/avif', 'image/webp'],
  },
  experimental: {
    // Enable if needed for Next.js 15 features
  },
  // Reduce file watcher load to prevent EMFILE errors
  webpack: (config, { dev, isServer }) => {
    if (dev && !isServer) {
      // Exclude certain directories from watching
      config.watchOptions = {
        ...config.watchOptions,
        ignored: [
          '**/node_modules/**',
          '**/.next/**',
          '**/dist/**',
          '**/build/**',
          '**/.git/**',
          '**/logs/**',
          '**/__tests__/**',
          '**/coverage/**',
        ],
        aggregateTimeout: 300,
        poll: false,
      }
    }
    return config
  },
}

module.exports = withSentryConfig(withBundleAnalyzer(nextConfig), {
  // Suppress Sentry CLI logs during build
  silent: true,
  // Disable source map upload in development (requires SENTRY_AUTH_TOKEN in CI)
  dryRun: process.env.NODE_ENV !== "production",
  // Automatically tree-shake Sentry logger statements
  disableLogger: true,
})
