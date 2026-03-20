"use client"

import { useQuery } from "@tanstack/react-query"
import Link from "next/link"
import { getSectorPeers } from "@/lib/api/stocks"

interface StockSectorOverviewProps {
  symbol: string
  sector: string | null
  industry: string | null
}

function fmtUSD(n: number | null): string {
  if (n === null) return "—"
  if (Math.abs(n) >= 1e12) return `$${(n / 1e12).toFixed(2)}T`
  if (Math.abs(n) >= 1e9) return `$${(n / 1e9).toFixed(2)}B`
  if (Math.abs(n) >= 1e6) return `$${(n / 1e6).toFixed(2)}M`
  return n.toLocaleString("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 2 })
}

function fmtPct(n: number | null): string {
  if (n === null) return "—"
  return `${n >= 0 ? "+" : ""}${n.toFixed(2)}%`
}

export function StockSectorOverview({ symbol, sector, industry }: StockSectorOverviewProps) {
  const { data: peers, isPending } = useQuery({
    queryKey: ["sector-peers", sector, symbol],
    queryFn: () => getSectorPeers(sector!, symbol, 10),
    staleTime: 5 * 60_000,
    enabled: !!sector,
  })

  if (!sector) return null

  return (
    <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-5">
      <div className="mb-4">
        <h2 className="text-sm font-semibold text-zinc-300 uppercase tracking-wide">
          Sector Overview
        </h2>
        <p className="text-zinc-500 text-xs mt-0.5">
          {sector}
          {industry ? ` · ${industry}` : ""}
        </p>
      </div>

      {isPending ? (
        <div className="animate-pulse space-y-2">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="h-10 rounded bg-zinc-800" />
          ))}
        </div>
      ) : !peers || peers.length === 0 ? (
        <p className="text-zinc-500 text-sm">No peers in this sector.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-zinc-800/60">
                <th className="text-left py-2 text-[11px] font-medium text-zinc-600 uppercase tracking-widest">
                  Symbol
                </th>
                <th className="text-right py-2 text-[11px] font-medium text-zinc-600 uppercase tracking-widest">
                  Price
                </th>
                <th className="text-right py-2 text-[11px] font-medium text-zinc-600 uppercase tracking-widest">
                  Day %
                </th>
                <th className="text-right py-2 text-[11px] font-medium text-zinc-600 uppercase tracking-widest">
                  P/E
                </th>
                <th className="text-right py-2 text-[11px] font-medium text-zinc-600 uppercase tracking-widest">
                  Mkt Cap
                </th>
              </tr>
            </thead>
            <tbody>
              {peers.map((peer) => (
                <tr
                  key={peer.symbol}
                  className={`border-b border-zinc-800/40 last:border-0 ${
                    peer.is_current ? "bg-zinc-800/40" : ""
                  }`}
                >
                  <td className="py-2.5">
                    <Link
                      href={`/stocks/${peer.symbol}`}
                      className={`font-mono font-medium hover:text-white transition-colors ${
                        peer.is_current ? "text-blue-400" : "text-zinc-300"
                      }`}
                    >
                      {peer.symbol}
                      {peer.is_current && " (you)"}
                    </Link>
                  </td>
                  <td className="py-2.5 text-right tabular-nums font-mono text-zinc-300">
                    {fmtUSD(peer.current_price)}
                  </td>
                  <td
                    className={`py-2.5 text-right tabular-nums text-xs font-medium ${
                      peer.day_change_percent != null
                        ? peer.day_change_percent >= 0
                          ? "text-green-400"
                          : "text-red-400"
                        : "text-zinc-500"
                    }`}
                  >
                    {fmtPct(peer.day_change_percent)}
                  </td>
                  <td className="py-2.5 text-right tabular-nums text-zinc-400">
                    {peer.pe_ratio != null ? `${peer.pe_ratio.toFixed(1)}x` : "—"}
                  </td>
                  <td className="py-2.5 text-right tabular-nums text-zinc-400 text-xs">
                    {fmtUSD(peer.market_cap)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
