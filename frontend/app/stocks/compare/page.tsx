"use client"

import { useSearchParams, useRouter } from "next/navigation"
import { Suspense, useState, useEffect } from "react"
import Link from "next/link"
import { ArrowLeft } from "lucide-react"
import { StockComparisonChart } from "@/components/features/stocks/StockComparisonChart"

const COLORS = ["#22c55e", "#3b82f6", "#f59e0b", "#ec4899", "#8b5cf6"]

function CompareContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const symbolsParam = searchParams.get("symbols") ?? ""
  const symbols = symbolsParam
    .split(",")
    .map((s) => s.trim().toUpperCase())
    .filter(Boolean)
    .slice(0, 5)

  const [inputValue, setInputValue] = useState(symbols.join(", "))
  const [activeSymbols, setActiveSymbols] = useState(symbols)

  useEffect(() => {
    setInputValue(symbols.join(", "))
    setActiveSymbols(symbols)
  }, [symbolsParam])

  const handleApply = () => {
    const parsed = inputValue
      .split(",")
      .map((s) => s.trim().toUpperCase())
      .filter(Boolean)
      .slice(0, 5)
    setActiveSymbols(parsed)
    router.push(`/stocks/compare?symbols=${parsed.join(",")}`)
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      <div className="max-w-5xl mx-auto px-4 py-6 space-y-4">
        <div className="flex items-center justify-between">
          <Link
            href="/stocks"
            className="flex items-center gap-1.5 text-zinc-400 hover:text-zinc-200 text-sm transition-colors"
          >
            <ArrowLeft size={15} />
            Back to Stocks
          </Link>
        </div>

        <div>
          <p className="text-[11px] font-medium tracking-widest uppercase text-zinc-500 mb-1">
            Compare
          </p>
          <h1 className="text-3xl font-bold tracking-tight">Stock Comparison</h1>
          <p className="text-sm text-zinc-500 mt-1">
            Compare up to 5 stocks. Enter symbols separated by commas.
          </p>
        </div>

        <div className="flex gap-2 flex-wrap">
          <input
            type="text"
            placeholder="e.g. AAPL, MSFT, GOOGL"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleApply()}
            className="flex-1 min-w-[200px] px-4 py-2 rounded-lg bg-zinc-800 border border-zinc-600 text-white placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleApply}
            className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm"
          >
            Compare
          </button>
        </div>

        {activeSymbols.length === 0 ? (
          <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-12 text-center">
            <p className="text-zinc-500">
              Enter stock symbols above to compare (e.g. AAPL, MSFT, GOOGL)
            </p>
          </div>
        ) : (
          <StockComparisonChart symbols={activeSymbols} colors={COLORS} />
        )}
      </div>
    </div>
  )
}

export default function StockComparePage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
          <div className="animate-pulse h-8 w-48 rounded bg-zinc-800" />
        </div>
      }
    >
      <CompareContent />
    </Suspense>
  )
}
