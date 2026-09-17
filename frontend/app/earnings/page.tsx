"use client"

import { useState } from "react"
import { useQuery, useQueries } from "@tanstack/react-query"
import { Calendar, TrendingUp, TrendingDown } from "lucide-react"
import { getPortfolio } from "@/lib/api/portfolio"
import { getWatchlists, getWatchlist } from "@/lib/api/watchlists"
import { useEarningsCalendar } from "@/lib/hooks/useEarnings"
import type { EarningsEvent } from "@/types/earnings"

function daysUntilBadge(days: number | null) {
  if (days == null) return null
  if (days <= 2) return "bg-red-400/10 text-red-400"
  if (days <= 7) return "bg-yellow-400/10 text-yellow-400"
  return "bg-zinc-700/50 text-zinc-400"
}

function EarningsRow({ event }: { event: EarningsEvent }) {
  const surprise = event.surprise_pct
  const hasSurprise = surprise != null

  return (
    <tr className="border-b border-zinc-800/50 transition-colors hover:bg-zinc-800/30">
      <td className="px-4 py-3 font-mono font-medium text-white">
        {event.symbol}
      </td>
      <td className="px-4 py-3 text-zinc-300">
        {new Date(event.earnings_date + "T00:00:00").toLocaleDateString(
          "en-US",
          {
            month: "short",
            day: "numeric",
            year: "numeric",
          }
        )}
      </td>
      <td className="px-4 py-3 text-right font-mono text-zinc-300 tabular-nums">
        {event.eps_estimate != null ? `$${event.eps_estimate.toFixed(2)}` : "—"}
      </td>
      <td className="px-4 py-3 text-right font-mono text-zinc-300 tabular-nums">
        {event.eps_actual != null ? `$${event.eps_actual.toFixed(2)}` : "—"}
      </td>
      <td className="px-4 py-3 text-right">
        {hasSurprise ? (
          <span
            className={`inline-flex items-center gap-1 font-mono text-xs font-medium tabular-nums ${
              surprise >= 0 ? "text-green-400" : "text-red-400"
            }`}
          >
            {surprise >= 0 ? (
              <TrendingUp className="h-3 w-3" />
            ) : (
              <TrendingDown className="h-3 w-3" />
            )}
            {surprise >= 0 ? "+" : ""}
            {surprise.toFixed(1)}%
          </span>
        ) : (
          <span className="text-zinc-600">—</span>
        )}
      </td>
      <td className="px-4 py-3 text-right">
        {event.is_upcoming && event.days_until != null ? (
          <span
            className={`inline-flex rounded px-2 py-0.5 text-xs font-medium ${daysUntilBadge(event.days_until)}`}
          >
            {event.days_until === 0
              ? "Today"
              : event.days_until === 1
                ? "Tomorrow"
                : `${event.days_until}d`}
          </span>
        ) : (
          <span className="text-xs text-zinc-600">Reported</span>
        )}
      </td>
    </tr>
  )
}

export default function EarningsPage() {
  const [tab, setTab] = useState<"upcoming" | "recent">("upcoming")

  // Gather symbols from portfolio + watchlist
  const { data: portfolio } = useQuery({
    queryKey: ["portfolio"],
    queryFn: getPortfolio,
  })
  const { data: watchlists } = useQuery({
    queryKey: ["watchlists"],
    queryFn: getWatchlists,
  })
  const watchlistDetailQueries = useQueries({
    queries: (watchlists ?? []).map((w) => ({
      queryKey: ["watchlist", w.id],
      queryFn: () => getWatchlist(w.id),
    })),
  })
  const watchlistSymbols = watchlistDetailQueries.flatMap(
    (q) => q.data?.items.map((item) => item.symbol) ?? []
  )

  const symbols = Array.from(
    new Set([
      ...(portfolio?.positions?.map((p: { symbol: string }) => p.symbol) ?? []),
      ...watchlistSymbols,
    ])
  )

  const { data: earnings, isPending } = useEarningsCalendar(symbols)

  // For "recent" tab, we need all events including past — the calendar endpoint only returns upcoming.
  // We show what we have from the calendar and label the tabs accordingly.
  const allEvents = earnings?.items ?? []
  const upcomingEvents = allEvents.filter((e) => e.is_upcoming)

  const displayEvents = tab === "upcoming" ? upcomingEvents : allEvents

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <div className="mb-6 flex items-center gap-3">
        <Calendar className="text-electric-400 h-6 w-6" />
        <h1 className="text-xl font-bold text-white">Earnings Calendar</h1>
        <span className="ml-2 text-xs text-zinc-500">
          {symbols.length} symbol{symbols.length !== 1 ? "s" : ""} tracked
        </span>
      </div>

      {/* Tabs */}
      <div className="mb-6 flex gap-1">
        {(["upcoming", "recent"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
              tab === t
                ? "bg-electric-500/10 text-electric-400 border-electric-500/20 border"
                : "text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-200"
            }`}
          >
            {t === "upcoming" ? "Upcoming" : "All"}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-xl border border-zinc-800 bg-zinc-900">
        {isPending ? (
          <div className="space-y-0">
            {Array.from({ length: 6 }).map((_, i) => (
              <div
                key={i}
                className="flex gap-4 border-b border-zinc-800/50 px-4 py-3"
              >
                <div className="h-4 w-16 animate-pulse rounded bg-zinc-800" />
                <div className="h-4 w-24 animate-pulse rounded bg-zinc-800" />
                <div className="ml-auto h-4 w-16 animate-pulse rounded bg-zinc-800" />
                <div className="h-4 w-16 animate-pulse rounded bg-zinc-800" />
                <div className="h-4 w-12 animate-pulse rounded bg-zinc-800" />
                <div className="h-4 w-14 animate-pulse rounded bg-zinc-800" />
              </div>
            ))}
          </div>
        ) : displayEvents.length === 0 ? (
          <div className="px-6 py-12 text-center text-zinc-500">
            <Calendar className="mx-auto mb-3 h-8 w-8 opacity-40" />
            <p className="text-sm">
              {symbols.length === 0
                ? "Add stocks to your portfolio or watchlist to see earnings dates."
                : "No upcoming earnings found for your tracked symbols."}
            </p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-zinc-800 bg-zinc-800/40 text-xs tracking-wider text-zinc-400 uppercase">
                <th className="px-4 py-2.5 text-left font-medium">Symbol</th>
                <th className="px-4 py-2.5 text-left font-medium">Date</th>
                <th className="px-4 py-2.5 text-right font-medium">EPS Est.</th>
                <th className="px-4 py-2.5 text-right font-medium">EPS Act.</th>
                <th className="px-4 py-2.5 text-right font-medium">Surprise</th>
                <th className="px-4 py-2.5 text-right font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {displayEvents.map((event, i) => (
                <EarningsRow
                  key={`${event.symbol}-${event.earnings_date}-${i}`}
                  event={event}
                />
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
