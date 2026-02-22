/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
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

module.exports = nextConfig
