import React from "react"
import { renderHook, act } from "@testing-library/react"
import { useWatchlist } from "@/lib/hooks/useWatchlist"
import { WatchlistProvider } from "@/lib/providers/WatchlistProvider"

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {}

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString()
    },
    removeItem: (key: string) => {
      delete store[key]
    },
    clear: () => {
      store = {}
    },
  }
})()

Object.defineProperty(window, "localStorage", {
  value: localStorageMock,
})

function TestWrapper({ children }: { children: React.ReactNode }) {
  return <WatchlistProvider>{children}</WatchlistProvider>
}

describe("useWatchlist", () => {
  beforeEach(() => {
    localStorageMock.clear()
  })

  it("initializes with empty watchlist", () => {
    const { result } = renderHook(() => useWatchlist(), { wrapper: TestWrapper })

    expect(result.current.watchlist).toEqual([])
    expect(result.current.getWatchlist()).toEqual([])
  })

  it("loads watchlist from localStorage on mount", () => {
    const storedWatchlist = ["AAPL", "MSFT", "GOOGL"]
    localStorageMock.setItem("stock-watchlist", JSON.stringify(storedWatchlist))

    const { result } = renderHook(() => useWatchlist(), { wrapper: TestWrapper })

    expect(result.current.watchlist).toEqual(storedWatchlist)
  })

  it("adds stock to watchlist", () => {
    const { result } = renderHook(() => useWatchlist(), { wrapper: TestWrapper })

    act(() => {
      result.current.addToWatchlist("AAPL")
    })

    expect(result.current.watchlist).toContain("AAPL")
    expect(result.current.isInWatchlist("AAPL")).toBe(true)
  })

  it("converts symbol to uppercase when adding", () => {
    const { result } = renderHook(() => useWatchlist(), { wrapper: TestWrapper })

    act(() => {
      result.current.addToWatchlist("aapl")
    })

    expect(result.current.watchlist).toContain("AAPL")
    expect(result.current.isInWatchlist("aapl")).toBe(true)
  })

  it("does not add duplicate stocks", () => {
    const { result } = renderHook(() => useWatchlist(), { wrapper: TestWrapper })

    act(() => {
      result.current.addToWatchlist("AAPL")
      result.current.addToWatchlist("AAPL")
    })

    expect(result.current.watchlist.filter((s) => s === "AAPL").length).toBe(1)
  })

  it("removes stock from watchlist", () => {
    const { result } = renderHook(() => useWatchlist(), { wrapper: TestWrapper })

    act(() => {
      result.current.addToWatchlist("AAPL")
      result.current.addToWatchlist("MSFT")
      result.current.removeFromWatchlist("AAPL")
    })

    expect(result.current.watchlist).not.toContain("AAPL")
    expect(result.current.watchlist).toContain("MSFT")
    expect(result.current.isInWatchlist("AAPL")).toBe(false)
  })

  it("toggles stock in watchlist", () => {
    const { result } = renderHook(() => useWatchlist(), { wrapper: TestWrapper })

    act(() => {
      result.current.toggleWatchlist("AAPL")
    })

    expect(result.current.isInWatchlist("AAPL")).toBe(true)

    act(() => {
      result.current.toggleWatchlist("AAPL")
    })

    expect(result.current.isInWatchlist("AAPL")).toBe(false)
  })

  it("saves watchlist to localStorage", () => {
    const { result } = renderHook(() => useWatchlist(), { wrapper: TestWrapper })

    act(() => {
      result.current.addToWatchlist("AAPL")
      result.current.addToWatchlist("MSFT")
    })

    const stored = localStorageMock.getItem("stock-watchlist")
    expect(stored).toBeTruthy()
    expect(JSON.parse(stored!)).toEqual(["AAPL", "MSFT"])
  })

  it("clears watchlist", () => {
    const { result } = renderHook(() => useWatchlist(), { wrapper: TestWrapper })

    act(() => {
      result.current.addToWatchlist("AAPL")
      result.current.addToWatchlist("MSFT")
      result.current.clearWatchlist()
    })

    expect(result.current.watchlist).toEqual([])
    expect(result.current.getWatchlist()).toEqual([])
  })

  it("handles invalid localStorage data gracefully", () => {
    localStorageMock.setItem("stock-watchlist", "invalid json")
    const consoleSpy = jest.spyOn(console, "error").mockImplementation(() => {})

    const { result } = renderHook(() => useWatchlist(), { wrapper: TestWrapper })

    // Should initialize with empty array on error
    expect(result.current.watchlist).toEqual([])
    consoleSpy.mockRestore()
  })
})
