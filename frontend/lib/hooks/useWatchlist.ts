"use client"

import { useWatchlistContext } from "@/lib/providers/WatchlistProvider"

/**
 * Shared watchlist state across all components.
 * Must be used within WatchlistProvider (wraps the app in layout).
 */
export function useWatchlist() {
  return useWatchlistContext()
}
