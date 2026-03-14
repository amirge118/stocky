"use client"

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react"

const WATCHLIST_STORAGE_KEY = "stock-watchlist"

interface WatchlistContextType {
  watchlist: string[]
  addToWatchlist: (symbol: string) => void
  removeFromWatchlist: (symbol: string) => void
  toggleWatchlist: (symbol: string) => void
  isInWatchlist: (symbol: string) => boolean
  getWatchlist: () => string[]
  clearWatchlist: () => void
}

const WatchlistContext = createContext<WatchlistContextType | null>(null)

export function WatchlistProvider({ children }: { children: React.ReactNode }) {
  const [watchlist, setWatchlist] = useState<string[]>([])

  useEffect(() => {
    try {
      const stored = localStorage.getItem(WATCHLIST_STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored) as string[]
        setWatchlist(Array.isArray(parsed) ? parsed : [])
      }
    } catch (error) {
      console.error("Failed to load watchlist from localStorage:", error)
      setWatchlist([])
    }
  }, [])

  useEffect(() => {
    try {
      localStorage.setItem(WATCHLIST_STORAGE_KEY, JSON.stringify(watchlist))
    } catch (error) {
      console.error("Failed to save watchlist to localStorage:", error)
    }
  }, [watchlist])

  const addToWatchlist = useCallback((symbol: string) => {
    setWatchlist((prev) => {
      const upperSymbol = symbol.toUpperCase()
      if (prev.includes(upperSymbol)) return prev
      return [...prev, upperSymbol]
    })
  }, [])

  const removeFromWatchlist = useCallback((symbol: string) => {
    setWatchlist((prev) =>
      prev.filter((s) => s !== symbol.toUpperCase())
    )
  }, [])

  const toggleWatchlist = useCallback((symbol: string) => {
    setWatchlist((prev) => {
      const upperSymbol = symbol.toUpperCase()
      if (prev.includes(upperSymbol)) {
        return prev.filter((s) => s !== upperSymbol)
      }
      return [...prev, upperSymbol]
    })
  }, [])

  const isInWatchlist = useCallback(
    (symbol: string) => watchlist.includes(symbol.toUpperCase()),
    [watchlist]
  )

  const getWatchlist = useCallback(() => [...watchlist], [watchlist])

  const clearWatchlist = useCallback(() => setWatchlist([]), [])

  return (
    <WatchlistContext.Provider
      value={{
        watchlist,
        addToWatchlist,
        removeFromWatchlist,
        toggleWatchlist,
        isInWatchlist,
        getWatchlist,
        clearWatchlist,
      }}
    >
      {children}
    </WatchlistContext.Provider>
  )
}

export function useWatchlistContext(): WatchlistContextType {
  const context = useContext(WatchlistContext)
  if (!context) {
    throw new Error("useWatchlistContext must be used within WatchlistProvider")
  }
  return context
}
