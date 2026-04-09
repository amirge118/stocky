"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { RefreshCw } from "lucide-react"
import { useQuery } from "@tanstack/react-query"
import { getMarketOverview } from "@/lib/api/market"
import { ApiError } from "@/lib/api/client"
import { IndicesStrip } from "@/components/features/market/IndicesStrip"
import { SectorHeatmap } from "@/components/features/market/SectorHeatmap"
import { TopMovers } from "@/components/features/market/TopMovers"
import { MarketSnapshotBar } from "@/components/features/market/MarketSnapshotBar"
import { MarketContextPanel } from "@/components/features/market/MarketContextPanel"
import type { MarketOverviewResponse } from "@/types/market"

const FIVE_MINUTES = 5 * 60 * 1000

const FALLBACK_TICKERS = [
  { symbol: "AAPL", price: "189.43", change: "+1.24%", up: true },
  { symbol: "NVDA", price: "875.39", change: "+3.61%", up: true },
  { symbol: "TSLA", price: "174.82", change: "-2.07%", up: false },
  { symbol: "MSFT", price: "418.56", change: "+0.93%", up: true },
  { symbol: "AMZN", price: "192.10", change: "+1.58%", up: true },
  { symbol: "GOOG", price: "163.74", change: "-0.44%", up: false },
  { symbol: "META", price: "523.90", change: "+2.12%", up: true },
  { symbol: "BRK", price: "412.00", change: "+0.31%", up: true },
]

function tickerFromOverview(data: MarketOverviewResponse | undefined) {
  if (!data) return FALLBACK_TICKERS
  const rows: { symbol: string; price: string; change: string; up: boolean }[] = []
  for (const idx of data.indices) {
    const up = idx.change_percent >= 0
    rows.push({
      symbol: idx.symbol,
      price: idx.price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
      change: `${up ? "+" : ""}${idx.change_percent.toFixed(2)}%`,
      up,
    })
  }
  const seen = new Set(rows.map((r) => r.symbol))
  for (const m of [...data.gainers, ...data.losers]) {
    if (seen.has(m.symbol)) continue
    seen.add(m.symbol)
    const up = m.change_percent >= 0
    rows.push({
      symbol: m.symbol,
      price: m.price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
      change: `${up ? "+" : ""}${m.change_percent.toFixed(2)}%`,
      up,
    })
  }
  return rows.length ? rows : FALLBACK_TICKERS
}

function TickerTape({
  items,
}: {
  items: { symbol: string; price: string; change: string; up: boolean }[]
}) {
  const loop = [...items, ...items, ...items]
  return (
    <div className="relative overflow-hidden border-y border-white/[0.06] bg-navy-900/50 py-2.5">
      <div className="flex animate-ticker whitespace-nowrap">
        {loop.map((t, i) => (
          <span key={i} className="inline-flex items-center gap-2 px-6 text-xs font-mono">
            <span className="text-zinc-200 font-semibold">{t.symbol}</span>
            <span className="text-zinc-400">{t.price}</span>
            <span className={t.up ? "text-mint-400" : "text-coral-400"}>{t.change}</span>
            <span className="text-zinc-700 mx-2">·</span>
          </span>
        ))}
      </div>
    </div>
  )
}

function MarketSkeleton() {
  return (
    <div className="space-y-8 animate-pulse">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-zinc-900 border border-zinc-800 rounded-lg h-24" />
        ))}
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
        {[...Array(11)].map((_, i) => (
          <div key={i} className="bg-zinc-900 border border-zinc-800 rounded-lg h-16" />
        ))}
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg h-56" />
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg h-56" />
      </div>
    </div>
  )
}

export default function HomePage() {
  const [mounted, setMounted] = useState(false)
  useEffect(() => {
    setMounted(true)
  }, [])

  const { data, isPending, isError, error, failureCount } = useQuery({
    queryKey: ["market-overview"],
    queryFn: getMarketOverview,
    staleTime: FIVE_MINUTES,
    refetchInterval: FIVE_MINUTES,
    retry: (count, err) => {
      // Render free tier cold starts can take up to 60s — retry for 12× @ 5s = 60s
      if (err instanceof ApiError && (err.status === 502 || err.status === 503)) {
        return count < 12
      }
      return false
    },
    retryDelay: 5000,
  })

  const isWarmingUp = isPending && error instanceof ApiError && (error.status === 502 || error.status === 503)

  const tickerItems = useMemo(() => tickerFromOverview(data), [data])

  return (
    <div className="min-h-screen bg-background text-white overflow-x-hidden">
      <TickerTape items={tickerItems} />

      <section className="relative flex flex-col items-center justify-center px-4 pt-14 pb-10 text-center">
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <div className="absolute left-1/4 top-1/4 h-[400px] w-[400px] rounded-full bg-electric-500/8 blur-[120px]" />
          <div className="absolute right-1/4 top-1/3 h-[300px] w-[300px] rounded-full bg-lime-500/6 blur-[100px]" />
        </div>

        <div
          className={`mb-5 flex h-14 w-14 items-center justify-center rounded-2xl glass shadow-glow-blue transition-all duration-700 ${mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"}`}
        >
          <svg viewBox="0 0 32 32" className="w-7 h-7" fill="none">
            <rect x="2" y="20" width="6" height="10" rx="1" fill="#38bdf8" />
            <rect x="11" y="13" width="6" height="17" rx="1" fill="#818cf8" />
            <rect x="20" y="6" width="6" height="24" rx="1" fill="#a78bfa" />
            <polyline
              points="5,18 14,11 23,4"
              stroke="#34d399"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              fill="none"
            />
            <circle cx="23" cy="4" r="2" fill="#34d399" />
          </svg>
        </div>

        <div
          className={`transition-all duration-700 delay-100 ${mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"}`}
        >
          <h1 className="text-4xl font-bold tracking-tight sm:text-5xl gradient-text-blue">Stocky</h1>
          <p className="mt-1 text-xs font-semibold tracking-[0.3em] uppercase text-zinc-500">
            Market snapshot &amp; tools
          </p>
        </div>

        <p
          className={`mt-5 max-w-xl text-base text-zinc-400 leading-relaxed transition-all duration-700 delay-200 ${mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"}`}
        >
          Live benchmarks, sector context when available, and mega-cap movers — a neutral read on
          broad market conditions.
        </p>

        <div
          className={`mt-8 flex flex-col sm:flex-row items-center gap-3 transition-all duration-700 delay-300 ${mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"}`}
        >
          <Link
            href="/portfolio"
            className="rounded-lg bg-electric-500 px-6 py-2.5 text-sm font-semibold text-white hover:bg-electric-400 shadow-glow-blue transition-all duration-200"
          >
            Portfolio
          </Link>
          <Link
            href="/watchlist"
            className="rounded-lg glass px-6 py-2.5 text-sm font-medium text-zinc-300 hover:border-white/20 hover:text-white transition-all duration-200"
          >
            Watchlist
          </Link>
        </div>
      </section>

      <main
        className={`mx-auto max-w-5xl px-4 pb-16 space-y-8 transition-all duration-700 delay-500 ${mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"}`}
      >
        <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <h2 className="text-xl font-bold text-white">Market Pulse</h2>
          {data && (
            <span className="text-xs text-zinc-500">
              Updated {new Date(data.updated_at).toLocaleString()}
            </span>
          )}
        </div>

        {isPending && !isWarmingUp && <MarketSkeleton />}

        {isWarmingUp && (
          <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-6 text-center space-y-2">
            <RefreshCw size={16} className="mx-auto text-zinc-500 animate-spin" />
            <p className="text-zinc-300 font-medium text-sm">Backend is warming up…</p>
            <p className="text-zinc-600 text-xs">Retrying automatically (attempt {failureCount} of 12)</p>
          </div>
        )}

        {isError && !isWarmingUp && (
          <div className="bg-red-950/40 border border-red-800 rounded-lg p-6 text-center space-y-2">
            <p className="text-red-400 font-medium">Failed to load market data.</p>
            <p className="text-red-500 text-sm">Please try again in a moment.</p>
          </div>
        )}

        {data && (
          <>
            <MarketSnapshotBar indices={data.indices} sectors={data.sectors} />
            <IndicesStrip indices={data.indices} />
            <SectorHeatmap sectors={data.sectors} />
            <TopMovers gainers={data.gainers} losers={data.losers} />
            <MarketContextPanel />
          </>
        )}
      </main>

      <section
        className={`mx-auto max-w-5xl px-4 pb-20 transition-all duration-700 delay-500 ${mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"}`}
      >
        <p className="text-center text-[11px] font-semibold tracking-widest uppercase text-zinc-600 mb-6">
          Also in Stocky
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-2xl mx-auto">
          <Link
            href="/watchlist"
            className="glass rounded-2xl p-5 hover-glow-blue transition-all hover:scale-[1.01] border border-white/[0.06]"
          >
            <p className="text-[11px] uppercase tracking-widest text-zinc-500 mb-1">Lists</p>
            <h3 className="text-sm font-semibold text-white mb-2">Watchlist</h3>
            <p className="text-xs text-zinc-500 leading-relaxed">Track symbols you care about in one place.</p>
          </Link>
          <Link
            href="/settings"
            className="glass rounded-2xl p-5 hover-glow-blue transition-all hover:scale-[1.01] border border-white/[0.06]"
          >
            <p className="text-[11px] uppercase tracking-widest text-zinc-500 mb-1">Account</p>
            <h3 className="text-sm font-semibold text-white mb-2">Settings</h3>
            <p className="text-xs text-zinc-500 leading-relaxed">Alerts, Telegram, and preferences.</p>
          </Link>
        </div>
      </section>

      <footer className="border-t border-white/[0.06] py-6 text-center text-xs text-zinc-600">
        Stocky · Built for traders who mean business
      </footer>
    </div>
  )
}
