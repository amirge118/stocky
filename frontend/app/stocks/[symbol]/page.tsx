"use client"

import { useParams, useRouter } from "next/navigation"
import { useQuery } from "@tanstack/react-query"
import { ArrowLeft, TrendingUp, TrendingDown } from "lucide-react"
import { getStock, fetchStockData, getStockInfo } from "@/lib/api/stocks"
import { StockChart } from "@/components/features/stocks/StockChart"
import { StockKeyStats } from "@/components/features/stocks/StockKeyStats"
import { StockAbout } from "@/components/features/stocks/StockAbout"
import { StockNews } from "@/components/features/stocks/StockNews"
import { StockAIAnalysis } from "@/components/features/stocks/StockAIAnalysis"
import { StockSectorOverview } from "@/components/features/stocks/StockSectorOverview"
import { StockDeepDiveCard } from "@/components/features/agents/StockDeepDiveCard"

export default function StockDetailPage() {
  const params = useParams()
  const symbol = params.symbol as string
  const router = useRouter()

  const { data: stock, isPending: stockLoading } = useQuery({
    queryKey: ["stock", symbol],
    queryFn: () => getStock(symbol),
  })

  const { data: liveData, isPending: liveLoading } = useQuery({
    queryKey: ["stock-data", symbol],
    queryFn: () => fetchStockData(symbol),
    staleTime: 60_000,
  })

  const { data: info, isPending: infoLoading } = useQuery({
    queryKey: ["stock-info", symbol],
    queryFn: () => getStockInfo(symbol),
    staleTime: 10 * 60_000,
  })

  const isPositive = liveData ? liveData.change >= 0 : true

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      <div className="max-w-5xl mx-auto px-4 py-6 space-y-4">

        {/* Back button */}
        <button
          onClick={() => router.back()}
          className="flex items-center gap-1.5 text-zinc-400 hover:text-zinc-200 text-sm transition-colors"
        >
          <ArrowLeft size={15} />
          Back
        </button>

        {/* Header */}
        <div>
          {stockLoading ? (
            <div className="animate-pulse space-y-2">
              <div className="h-8 bg-zinc-800 rounded w-32" />
              <div className="h-5 bg-zinc-800 rounded w-48" />
            </div>
          ) : (
            <>
              <div className="flex items-baseline gap-3 flex-wrap">
                <h1 className="text-4xl font-bold tracking-tight">{symbol.toUpperCase()}</h1>
                {stock && <span className="text-xl text-zinc-400">{stock.name}</span>}
              </div>

              <div className="flex items-center gap-3 flex-wrap mt-1.5">
                {liveLoading ? (
                  <div className="animate-pulse h-8 bg-zinc-800 rounded w-28" />
                ) : liveData ? (
                  <>
                    <span className="text-3xl font-semibold">
                      ${liveData.current_price.toFixed(2)}
                    </span>
                    <span
                      className={`flex items-center gap-1 text-sm font-medium px-2 py-0.5 rounded-md ${
                        isPositive
                          ? "text-green-400 bg-green-400/10"
                          : "text-red-400 bg-red-400/10"
                      }`}
                    >
                      {isPositive ? <TrendingUp size={13} /> : <TrendingDown size={13} />}
                      {isPositive ? "+" : ""}{liveData.change.toFixed(2)} ({isPositive ? "+" : ""}{liveData.change_percent.toFixed(2)}%)
                    </span>
                    {stock?.exchange && (
                      <span className="text-xs text-zinc-500">{stock.exchange}</span>
                    )}
                  </>
                ) : null}
              </div>
            </>
          )}
        </div>

        {/* About — compact strip above chart */}
        {infoLoading ? (
          <div className="animate-pulse h-10 rounded-xl bg-zinc-900 border border-zinc-800" />
        ) : info ? (
          <StockAbout info={info} compact />
        ) : null}

        {/* Chart — half height */}
        <StockChart symbol={symbol} />

        {/* Key Stats + News — side by side */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {infoLoading ? (
            <div className="animate-pulse rounded-xl bg-zinc-900 border border-zinc-800 h-52" />
          ) : info ? (
            <StockKeyStats info={info} />
          ) : null}

          <StockNews symbol={symbol} />
        </div>

        {/* AI Analysis */}
        <StockAIAnalysis symbol={symbol} />

        {/* Deep Dive Agent */}
        <StockDeepDiveCard symbol={symbol} />

        {/* Sector Overview */}
        {info && (
          <StockSectorOverview
            symbol={symbol}
            sector={info.sector}
            industry={info.industry}
          />
        )}
      </div>
    </div>
  )
}
