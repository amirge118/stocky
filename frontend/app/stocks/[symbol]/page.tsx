"use client"

import { useParams, useRouter } from "next/navigation"
import { useQuery } from "@tanstack/react-query"
import { ArrowLeft, ExternalLink } from "lucide-react"
import { LivePriceBadge } from "@/components/features/stocks/LivePriceBadge"
import { getStock, fetchStockData, getStockInfo } from "@/lib/api/stocks"
import { ApiError } from "@/lib/api/client"
import { StockChart } from "@/components/features/stocks/StockChart"
import { StockIndicators } from "@/components/features/stocks/StockIndicators"
import { StockKeyStats } from "@/components/features/stocks/StockKeyStats"
import { StockAbout } from "@/components/features/stocks/StockAbout"
import { StockNews } from "@/components/features/stocks/StockNews"
import { SectorNews } from "@/components/features/stocks/SectorNews"
import { StockAIAnalysis } from "@/components/features/stocks/StockAIAnalysis"
import { StockSectorOverview } from "@/components/features/stocks/StockSectorOverview"
import { StockDividends } from "@/components/features/stocks/StockDividends"
import { StockAlertsSection } from "@/components/features/stocks/StockAlertsSection"

export default function StockDetailPage() {
  const params = useParams()
  const symbol = params.symbol as string
  const router = useRouter()

  const { data: stock, isPending: stockLoading } = useQuery({
    queryKey: ["stock", symbol],
    queryFn: () => getStock(symbol),
  })

  const { data: liveData, isPending: liveLoading, error: liveError } = useQuery({
    queryKey: ["stock-data", symbol],
    queryFn: () => fetchStockData(symbol),
    staleTime: 60_000,
    retry: 1,
  })

  const { data: info, isPending: infoLoading } = useQuery({
    queryKey: ["stock-info", symbol],
    queryFn: () => getStockInfo(symbol),
    staleTime: 10 * 60_000,
  })

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      <div className="max-w-5xl mx-auto px-4 py-6 space-y-4">

        {/* Back button */}
        <div className="flex items-center">
          <button
            onClick={() => router.back()}
            className="flex items-center gap-1.5 text-zinc-400 hover:text-zinc-200 text-sm transition-colors"
          >
            <ArrowLeft size={15} />
            Back
          </button>
        </div>

        {/* Data unavailable banner */}
        {liveError && !liveLoading && (
          <div className="rounded-lg border border-amber-800/50 bg-amber-950/30 px-4 py-3 text-sm text-amber-300">
            {liveError instanceof ApiError && liveError.status === 503
              ? "Market data is temporarily unavailable — daily API quota reached. Prices will refresh when the quota resets (midnight UTC)."
              : liveError instanceof ApiError && (liveError.status === 404 || liveError.status === 402)
              ? `Live price data for ${symbol.toUpperCase()} is not available on the current data plan. Only major US equities are supported.`
              : "Live price data is temporarily unavailable."}
          </div>
        )}

        {/* Header */}
        <div>
          {stockLoading ? (
            <div className="animate-pulse space-y-2">
              <div className="h-8 bg-zinc-800 rounded w-32" />
              <div className="h-5 bg-zinc-800 rounded w-48" />
            </div>
          ) : (
            <>
              <div className="flex items-baseline justify-between gap-3 flex-wrap">
                <div className="flex items-baseline gap-3 flex-wrap">
                  <h1 className="text-4xl font-bold tracking-tight">{symbol.toUpperCase()}</h1>
                  {stock && <span className="text-xl text-zinc-400">{stock.name}</span>}
                </div>
                {/* Tags + Website — right of company name */}
                {info && (
                  <div className="flex items-center gap-2 flex-wrap shrink-0">
                    {info.sector && (
                      <span className="text-xs text-zinc-300 bg-zinc-800 px-2 py-0.5 rounded-full">
                        {info.sector}
                      </span>
                    )}
                    {info.industry && (
                      <span className="text-xs text-zinc-400 bg-zinc-800/60 px-2 py-0.5 rounded-full">
                        {info.industry}
                      </span>
                    )}
                    {info.country && (
                      <span className="text-xs text-zinc-500 bg-zinc-800/40 px-2 py-0.5 rounded-full">
                        {info.country}
                      </span>
                    )}
                    {info.website && (
                      <a
                        href={info.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-0.5 transition-colors"
                      >
                        {info.website.replace(/^https?:\/\//, "").replace(/\/$/, "").split("/")[0]}
                        <ExternalLink size={10} />
                      </a>
                    )}
                  </div>
                )}
              </div>

              <div className="flex items-center gap-3 flex-wrap mt-1.5">
                {liveLoading && !liveData ? (
                  <div className="animate-pulse h-8 bg-zinc-800 rounded w-28" />
                ) : (
                  <LivePriceBadge
                    symbol={symbol}
                    fallbackPrice={liveData?.current_price}
                    fallbackChange={liveData?.change}
                    fallbackChangePercent={liveData?.change_percent}
                    currency={liveData?.currency}
                  />
                )}
                {stock?.exchange && (
                  <span className="text-xs text-zinc-500">{stock.exchange}</span>
                )}
              </div>
            </>
          )}
        </div>

        {/* Left: Description + Chart + Key Stats | Right: News */}
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_300px] gap-4">
          <div className="space-y-4">
            {/* About — compact strip above chart */}
            {infoLoading ? (
              <div className="animate-pulse h-10 rounded-xl bg-zinc-900 border border-zinc-800" />
            ) : info ? (
              <StockAbout info={info} compact />
            ) : null}

            {/* Chart */}
            <StockChart symbol={symbol} currency={liveData?.currency} />

            {/* Technical Indicators */}
            <StockIndicators symbol={symbol} />

            {/* Key Stats — 2–3 rows below chart */}
            {infoLoading ? (
              <div className="rounded-xl bg-zinc-900 border border-zinc-800 px-4 py-3 animate-pulse">
                <div className="h-3 w-24 rounded bg-zinc-800 mb-3" />
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-x-6 gap-y-2.5">
                  {Array.from({ length: 8 }).map((_, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <div className="h-3 w-12 rounded bg-zinc-800" />
                      <div className="h-3 w-10 rounded bg-zinc-700" />
                    </div>
                  ))}
                </div>
              </div>
            ) : info ? (
              <StockKeyStats info={info} compact currency={liveData?.currency} />
            ) : null}

            {/* Dividends */}
            <StockDividends symbol={symbol} />
          </div>

          <div className="lg:min-h-0 space-y-4">
            {/* Alerts */}
            <StockAlertsSection symbol={symbol} currentPrice={liveData?.current_price} />
            <StockNews symbol={symbol} />
            {info?.sector && <SectorNews sector={info.sector} />}
          </div>
        </div>

        {/* AI Analysis */}
        <StockAIAnalysis symbol={symbol} />

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
