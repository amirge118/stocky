"use client"

import { useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { useQuery } from "@tanstack/react-query"
import { ArrowLeft, Bell, ExternalLink } from "lucide-react"
import { Button } from "@/components/ui/button"
import { AlertDialog } from "@/components/features/stocks/AlertDialog"
import { LivePriceBadge } from "@/components/features/stocks/LivePriceBadge"
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
  const [alertDialogOpen, setAlertDialogOpen] = useState(false)

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

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      <div className="max-w-5xl mx-auto px-4 py-6 space-y-4">

        {/* Back button + Alert */}
        <div className="flex items-center justify-between">
          <button
            onClick={() => router.back()}
            className="flex items-center gap-1.5 text-zinc-400 hover:text-zinc-200 text-sm transition-colors"
          >
            <ArrowLeft size={15} />
            Back
          </button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAlertDialogOpen(true)}
            className="border-zinc-600 text-zinc-300 hover:bg-zinc-800"
          >
            <Bell size={14} className="mr-1.5" />
            Price Alert
          </Button>
        </div>

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
            <StockChart symbol={symbol} />

            {/* Key Stats — 2–3 rows below chart */}
            {infoLoading ? (
              <div className="animate-pulse rounded-xl bg-zinc-900 border border-zinc-800 h-24" />
            ) : info ? (
              <StockKeyStats info={info} compact />
            ) : null}
          </div>

          <div className="lg:min-h-0">
            <StockNews symbol={symbol} />
          </div>
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

        <AlertDialog
          open={alertDialogOpen}
          onOpenChange={setAlertDialogOpen}
          symbol={symbol}
        />
      </div>
    </div>
  )
}
