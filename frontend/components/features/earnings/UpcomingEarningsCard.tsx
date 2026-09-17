"use client"

import Link from "next/link"
import { Calendar } from "lucide-react"
import { useEarningsCalendar } from "@/lib/hooks/useEarnings"

interface Props {
  symbols: string[]
}

export function UpcomingEarningsCard({ symbols }: Props) {
  const { data, isPending } = useEarningsCalendar(symbols)

  const upcoming = (data?.items ?? []).filter((e) => e.is_upcoming).slice(0, 5)

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Calendar className="text-electric-400 h-4 w-4" />
          <h3 className="text-sm font-medium text-white">Upcoming Earnings</h3>
        </div>
        <Link
          href="/earnings"
          className="text-xs text-zinc-500 transition-colors hover:text-zinc-300"
        >
          View all
        </Link>
      </div>

      {isPending ? (
        <div className="space-y-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="flex justify-between">
              <div className="h-3.5 w-12 animate-pulse rounded bg-zinc-800" />
              <div className="h-3.5 w-20 animate-pulse rounded bg-zinc-800" />
            </div>
          ))}
        </div>
      ) : upcoming.length === 0 ? (
        <p className="text-xs text-zinc-500">No upcoming earnings</p>
      ) : (
        <div className="space-y-1.5">
          {upcoming.map((e) => (
            <div
              key={`${e.symbol}-${e.earnings_date}`}
              className="flex items-center justify-between text-xs"
            >
              <span className="font-mono font-medium text-white">
                {e.symbol}
              </span>
              <div className="flex items-center gap-2">
                <span className="text-zinc-400">
                  {new Date(e.earnings_date + "T00:00:00").toLocaleDateString(
                    "en-US",
                    {
                      month: "short",
                      day: "numeric",
                    }
                  )}
                </span>
                {e.days_until != null && (
                  <span
                    className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${
                      e.days_until <= 2
                        ? "bg-red-400/10 text-red-400"
                        : e.days_until <= 7
                          ? "bg-yellow-400/10 text-yellow-400"
                          : "bg-zinc-700/50 text-zinc-500"
                    }`}
                  >
                    {e.days_until === 0 ? "Today" : `${e.days_until}d`}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
