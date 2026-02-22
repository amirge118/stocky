"use client"

import { useState, useEffect, useCallback } from "react"

const WATCHLIST_STORAGE_KEY = "stock-watchlist"

export function useWatchlist() {
  const [watchlist, setWatchlist] = useState<string[]>([])

  // Load watchlist from localStorage on mount
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

  // Save watchlist to localStorage whenever it changes
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
      if (prev.includes(upperSymbol)) {
        return prev
      }
      return [...prev, upperSymbol]
    })
  }, [])

  const removeFromWatchlist = useCallback((symbol: string) => {
    setWatchlist((prev) => {
      const upperSymbol = symbol.toUpperCase()
      return prev.filter((s) => s !== upperSymbol)
    })
  }, [])

  const toggleWatchlist = useCallback(
    (symbol: string) => {
      const upperSymbol = symbol.toUpperCase()
      if (watchlist.includes(upperSymbol)) {
        removeFromWatchlist(upperSymbol)
      } else {
        addToWatchlist(upperSymbol)
      }
    },
    [watchlist, addToWatchlist, removeFromWatchlist]
  )

  const isInWatchlist = useCallback(
    (symbol: string) => {
      return watchlist.includes(symbol.toUpperCase())
    },
    [watchlist]
  )

  const getWatchlist = useCallback(() => {
    return [...watchlist]
  }, [watchlist])

  const clearWatchlist = useCallback(() => {
    setWatchlist([])
  }, [])

  return {
    watchlist,
    addToWatchlist,
    removeFromWatchlist,
    toggleWatchlist,
    isInWatchlist,
    getWatchlist,
    clearWatchlist,
  }
}
