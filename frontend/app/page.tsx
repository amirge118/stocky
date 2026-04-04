"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { getMarketOverview } from "@/lib/api/market"

const TICKERS = [
  { symbol: "AAPL", price: "189.43", change: "+1.24%", up: true },
  { symbol: "NVDA", price: "875.39", change: "+3.61%", up: true },
  { symbol: "TSLA", price: "174.82", change: "-2.07%", up: false },
  { symbol: "MSFT", price: "418.56", change: "+0.93%", up: true },
  { symbol: "AMZN", price: "192.10", change: "+1.58%", up: true },
  { symbol: "GOOG", price: "163.74", change: "-0.44%", up: false },
  { symbol: "META", price: "523.90", change: "+2.12%", up: true },
  { symbol: "BRK",  price: "412.00", change: "+0.31%", up: true },
]

const INDICES = [
  { label: "S&P 500", value: "5,234.18", change: "+0.87%", up: true },
  { label: "NASDAQ",  value: "16,428.82", change: "+1.14%", up: true },
  { label: "DOW",     value: "39,112.76", change: "+0.42%", up: true },
  { label: "VIX",     value: "14.32", change: "-3.21%", up: false },
]

const SECTORS = [
  { name: "Tech",       change: "+2.1%", up: true },
  { name: "Energy",     change: "-0.8%", up: false },
  { name: "Finance",    change: "+1.3%", up: true },
  { name: "Healthcare", change: "+0.5%", up: true },
  { name: "Consumer",   change: "-0.3%", up: false },
  { name: "Utilities",  change: "+0.2%", up: true },
]

const MOCK_PORTFOLIO = [
  { symbol: "AAPL", shares: 12, price: "189.43", gain: "+4.2%", up: true },
  { symbol: "NVDA", shares: 5,  price: "875.39", gain: "+18.7%", up: true },
  { symbol: "TSLA", shares: 8,  price: "174.82", gain: "-6.1%",  up: false },
]

function TickerTape() {
  return (
    <div className="relative overflow-hidden border-y border-white/[0.06] bg-navy-900/50 py-2.5">
      <div className="flex animate-ticker whitespace-nowrap">
        {[...TICKERS, ...TICKERS, ...TICKERS].map((t, i) => (
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

export default function HomePage() {
  const [mounted, setMounted] = useState(false)
  useEffect(() => { setMounted(true) }, [])

  const { data: marketData } = useQuery({
    queryKey: ["market-overview"],
    queryFn: getMarketOverview,
    staleTime: 5 * 60_000,
  })

  const displayIndices = marketData?.indices.slice(0, 4).map((idx) => ({
    label: idx.name,
    value: idx.price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
    change: `${idx.change_percent >= 0 ? "+" : ""}${idx.change_percent.toFixed(2)}%`,
    up: idx.change_percent >= 0,
  })) ?? INDICES

  const displaySectors = marketData?.sectors.slice(0, 6).map((s) => ({
    name: s.name,
    change: `${s.change_percent >= 0 ? "+" : ""}${s.change_percent.toFixed(2)}%`,
    up: s.change_percent >= 0,
  })) ?? SECTORS

  return (
    <div className="min-h-screen bg-background text-white overflow-x-hidden">

      {/* Ticker tape */}
      <TickerTape />

      {/* Hero */}
      <section className="relative flex flex-col items-center justify-center px-4 pt-20 pb-14 text-center">

        {/* Background glow orbs */}
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <div className="absolute left-1/4 top-1/4 h-[400px] w-[400px] rounded-full bg-electric-500/8 blur-[120px]" />
          <div className="absolute right-1/4 top-1/3 h-[300px] w-[300px] rounded-full bg-lime-500/6 blur-[100px]" />
        </div>

        {/* Logo mark */}
        <div
          className={`mb-6 flex h-16 w-16 items-center justify-center rounded-2xl glass shadow-glow-blue transition-all duration-700 ${mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"}`}
        >
          <svg viewBox="0 0 32 32" className="w-8 h-8" fill="none">
            <rect x="2" y="20" width="6" height="10" rx="1" fill="#38bdf8" />
            <rect x="11" y="13" width="6" height="17" rx="1" fill="#818cf8" />
            <rect x="20" y="6"  width="6" height="24" rx="1" fill="#a78bfa" />
            <polyline points="5,18 14,11 23,4" stroke="#34d399" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
            <circle cx="23" cy="4" r="2" fill="#34d399" />
          </svg>
        </div>

        {/* Wordmark */}
        <div className={`transition-all duration-700 delay-100 ${mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"}`}>
          <h1 className="text-6xl font-bold tracking-tight sm:text-7xl gradient-text-blue">
            Stocky
          </h1>
          <p className="mt-1 text-xs font-semibold tracking-[0.3em] uppercase text-zinc-500">
            Financial Intelligence Platform
          </p>
        </div>

        {/* Tagline */}
        <p className={`mt-6 max-w-xl text-lg text-zinc-400 leading-relaxed transition-all duration-700 delay-200 ${mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"}`}>
          Portfolio tracking, AI-powered analysis, and real-time price alerts —
          everything you need to stay ahead of the market.
        </p>

        {/* CTAs */}
        <div className={`mt-10 flex flex-col sm:flex-row items-center gap-3 transition-all duration-700 delay-300 ${mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"}`}>
          <Link
            href="/portfolio"
            className="rounded-lg bg-electric-500 px-6 py-2.5 text-sm font-semibold text-white hover:bg-electric-400 shadow-glow-blue transition-all duration-200"
          >
            Open Portfolio
          </Link>
          <Link
            href="/market"
            className="rounded-lg glass px-6 py-2.5 text-sm font-medium text-zinc-300 hover:border-white/20 hover:text-white transition-all duration-200"
          >
            View Market
          </Link>
        </div>
      </section>

      {/* Bento Grid */}
      <section className={`mx-auto max-w-5xl px-4 pb-24 transition-all duration-700 delay-500 ${mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"}`}>
        <p className="text-center text-[11px] font-semibold tracking-widest uppercase text-zinc-600 mb-6">
          Everything you need
        </p>

        <div className="bento-grid">

          {/* Cell A — Portfolio Preview (col-span-3, row-span-2) */}
          <div className="col-span-6 sm:col-span-3 row-span-2 glass rounded-2xl p-5 hover-glow-blue transition-all duration-300 hover:scale-[1.01] flex flex-col">
            <p className="text-[11px] uppercase tracking-widest text-zinc-500 mb-1">Feature</p>
            <h3 className="text-sm font-semibold text-white tracking-tight mb-1">Portfolio Tracker</h3>
            <p className="text-xs text-zinc-500 leading-relaxed mb-4">
              Monitor your positions, P&amp;L, and sector exposure in real time.
            </p>

            {/* Mock ticker rows */}
            <div className="flex-1 flex flex-col gap-2">
              {MOCK_PORTFOLIO.map((row) => (
                <div key={row.symbol} className="flex items-center justify-between rounded-xl bg-white/[0.03] border border-white/[0.06] px-3 py-2">
                  <div className="flex items-center gap-3">
                    <div className="h-7 w-7 rounded-lg bg-electric-500/15 flex items-center justify-center">
                      <span className="text-[10px] font-bold text-electric-400">{row.symbol[0]}</span>
                    </div>
                    <div>
                      <div className="text-xs font-semibold font-mono text-white">{row.symbol}</div>
                      <div className="text-[10px] text-zinc-500">{row.shares} shares</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs font-mono text-zinc-200">${row.price}</div>
                    <div className={`text-[10px] font-mono font-medium ${row.up ? "text-mint-400" : "text-coral-400"}`}>{row.gain}</div>
                  </div>
                </div>
              ))}
            </div>

            <Link
              href="/portfolio"
              className="mt-4 inline-flex items-center gap-1 text-xs font-semibold text-electric-400 hover:text-electric-300 transition-colors"
            >
              Open Portfolio <span>→</span>
            </Link>
          </div>

          {/* Cell B — Market Indices (col-span-2) */}
          <div className="col-span-6 sm:col-span-2 glass rounded-2xl p-5 hover-glow-blue transition-all duration-300 hover:scale-[1.01]">
            <p className="text-[11px] uppercase tracking-widest text-zinc-500 mb-1">Live</p>
            <h3 className="text-sm font-semibold text-white tracking-tight mb-3">Market Indices</h3>
            <div className="flex flex-col gap-2">
              {displayIndices.map((idx) => (
                <div key={idx.label} className="flex items-center justify-between">
                  <span className="text-xs text-zinc-400">{idx.label}</span>
                  <div className="text-right">
                    <div className="text-xs font-mono text-zinc-200">{idx.value}</div>
                    <div className={`text-[10px] font-mono ${idx.up ? "text-mint-400" : "text-coral-400"}`}>{idx.change}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Cell C — AI on stock pages (col-span-1) */}
          <div className="col-span-6 sm:col-span-1 glass rounded-2xl p-5 hover-glow-blue transition-all duration-300 hover:scale-[1.01] flex flex-col">
            <div className="h-8 w-8 rounded-xl bg-rose-500/15 flex items-center justify-center mb-3">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} className="w-4 h-4 text-rose-400">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 0 0-2.456 2.456Z" />
              </svg>
            </div>
            <p className="text-[11px] uppercase tracking-widest text-zinc-500 mb-1">AI</p>
            <h3 className="text-sm font-semibold text-white tracking-tight mb-1">Stock insight</h3>
            <p className="text-xs text-zinc-500 leading-relaxed flex-1">Open any ticker for AI analysis on its page.</p>
            <Link href="/market" className="mt-3 text-[10px] text-rose-400 hover:text-rose-300 transition-colors">
              Market overview →
            </Link>
          </div>

          {/* Cell D — Alerts (col-span-2) */}
          <div className="col-span-6 sm:col-span-2 glass rounded-2xl p-5 hover-glow-blue transition-all duration-300 hover:scale-[1.01] flex flex-col gap-2">
            <div className="flex items-center gap-2 mb-1">
              <div className="h-7 w-7 rounded-lg bg-amber-500/15 flex items-center justify-center">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} className="w-3.5 h-3.5 text-amber-400">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0" />
                </svg>
              </div>
              <div>
                <p className="text-[11px] uppercase tracking-widest text-zinc-500">Notifications</p>
                <h3 className="text-sm font-semibold text-white tracking-tight">Price Alerts</h3>
              </div>
            </div>
            <p className="text-xs text-zinc-500 leading-relaxed">
              Get Telegram notifications the moment a stock crosses your target.
            </p>
            <Link href="/alerts" className="mt-auto text-[10px] text-amber-400 hover:text-amber-300 transition-colors">
              Set alert →
            </Link>
          </div>

          {/* Cell E — Market Pulse heatmap (col-span-3) */}
          <div className="col-span-6 sm:col-span-3 glass rounded-2xl p-5 hover-glow-blue transition-all duration-300 hover:scale-[1.01]">
            <p className="text-[11px] uppercase tracking-widest text-zinc-500 mb-1">Heatmap</p>
            <h3 className="text-sm font-semibold text-white tracking-tight mb-3">Market Pulse</h3>
            <div className="grid grid-cols-3 gap-1.5">
              {displaySectors.map((s) => (
                <div
                  key={s.name}
                  className={`rounded-lg px-2 py-2 text-center ${
                    s.up
                      ? "bg-mint-500/10 border border-mint-500/20"
                      : "bg-coral-500/10 border border-coral-500/20"
                  }`}
                >
                  <div className="text-[10px] text-zinc-400">{s.name}</div>
                  <div className={`text-xs font-mono font-semibold ${s.up ? "text-mint-400" : "text-coral-400"}`}>
                    {s.change}
                  </div>
                </div>
              ))}
            </div>
            <Link href="/market" className="mt-3 inline-block text-[10px] text-electric-400 hover:text-electric-300 transition-colors">
              Full market view →
            </Link>
          </div>

        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/[0.06] py-6 text-center text-xs text-zinc-600">
        Stocky · Built for traders who mean business
      </footer>
    </div>
  )
}
