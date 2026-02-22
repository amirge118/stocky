"use client"

import { useQueryClient } from "@tanstack/react-query"
import Link from "next/link"
import type { StockListResponse } from "@/types/stock"

interface StockSectorOverviewProps {
  symbol: string
  sector: string | null
  industry: string | null
}

export function StockSectorOverview({ symbol, sector, industry }: StockSectorOverviewProps) {
  const queryClient = useQueryClient()

  if (!sector) return null

  // Reuse cached stocks list from the main page — no extra fetch
  const cached = queryClient.getQueryData<StockListResponse>(["stocks"])
  const peers = cached?.data.filter(
    (s) => s.sector === sector && s.symbol !== symbol
  ) ?? []

  return (
    <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-5">
      <h2 className="text-sm font-semibold text-zinc-300 uppercase tracking-wide mb-1">Sector Overview</h2>
      <p className="text-zinc-500 text-xs mb-4">
        {sector}{industry ? ` · ${industry}` : ""}
      </p>

      {peers.length === 0 ? (
        <p className="text-zinc-500 text-sm">No peers in your watchlist for this sector.</p>
      ) : (
        <ul className="divide-y divide-zinc-800">
          {peers.map((peer) => (
            <li key={peer.symbol} className="py-2 first:pt-0 last:pb-0">
              <Link
                href={`/stocks/${peer.symbol}`}
                className="flex items-center justify-between group"
              >
                <div>
                  <span className="text-white font-medium text-sm group-hover:text-zinc-200 transition-colors">
                    {peer.symbol}
                  </span>
                  <p className="text-zinc-500 text-xs">{peer.name}</p>
                </div>
                <span className="text-zinc-400 text-xs">{peer.exchange}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
