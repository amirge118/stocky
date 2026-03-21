"use client"
import { useState, useEffect, useRef, useCallback } from "react"
import { useRouter } from "next/navigation"
import { Search } from "lucide-react"
import { searchStocks } from "@/lib/api/stocks"
import type { StockSearchResult } from "@/types/stock"

export function GlobalStockSearch() {
  const router = useRouter()
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<StockSearchResult[]>([])
  const [isOpen, setIsOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [highlighted, setHighlighted] = useState(-1)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault()
        inputRef.current?.focus()
        inputRef.current?.select()
      }
    }
    document.addEventListener("keydown", handleKeyDown)
    return () => document.removeEventListener("keydown", handleKeyDown)
  }, [])

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    const trimmed = query.trim()
    if (trimmed.length < 1 || !/^[\x00-\x7F]+$/.test(trimmed)) { setResults([]); setIsOpen(false); return }
    setIsLoading(true)
    debounceRef.current = setTimeout(async () => {
      try {
        const data = await searchStocks(trimmed)
        setResults(data.slice(0, 6))
        setIsOpen(data.length > 0)
        setHighlighted(-1)
      } catch { setResults([]) }
      finally { setIsLoading(false) }
    }, 350)
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current) }
  }, [query])

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener("mousedown", handler)
    return () => document.removeEventListener("mousedown", handler)
  }, [])

  const navigate = useCallback((symbol: string) => {
    setQuery("")
    setResults([])
    setIsOpen(false)
    router.push(`/stocks/${symbol}`)
  }, [router])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) return
    if (e.key === "ArrowDown") { e.preventDefault(); setHighlighted(h => Math.min(h + 1, results.length - 1)) }
    else if (e.key === "ArrowUp") { e.preventDefault(); setHighlighted(h => Math.max(h - 1, -1)) }
    else if (e.key === "Enter" && highlighted >= 0) { navigate(results[highlighted].symbol) }
    else if (e.key === "Escape") { setIsOpen(false); setQuery("") }
  }

  return (
    <div ref={containerRef} className="relative w-48 lg:w-64">
      <div className="relative">
        <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-zinc-500 pointer-events-none" />
        <input
          ref={inputRef}
          type="text"
          placeholder="Search stocks..."
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => results.length > 0 && setIsOpen(true)}
          className="w-full h-8 pl-8 pr-3 rounded-lg bg-zinc-800 border border-zinc-700 text-sm text-white placeholder:text-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
        />
        {isLoading && (
          <div className="absolute right-2.5 top-1/2 -translate-y-1/2 h-3 w-3 rounded-full border border-zinc-500 border-t-transparent animate-spin" />
        )}
      </div>
      {isOpen && results.length > 0 && (
        <div className="absolute top-full mt-1 left-0 right-0 z-50 rounded-xl border border-zinc-700 bg-zinc-900 shadow-xl overflow-hidden">
          {results.map((r, i) => (
            <button
              key={r.symbol}
              onClick={() => navigate(r.symbol)}
              className={`w-full flex items-center gap-3 px-3 py-2 text-left transition-colors ${i === highlighted ? "bg-zinc-700" : "hover:bg-zinc-800"}`}
            >
              <span className="font-mono text-xs font-semibold text-white w-14 shrink-0">{r.symbol}</span>
              <span className="text-xs text-zinc-400 truncate flex-1">{r.name}</span>
              {r.current_price != null && (
                <span className="text-xs font-mono text-zinc-300 shrink-0">
                  {r.currency === "ILS" ? "₪" : "$"}{r.current_price.toFixed(2)}
                </span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
