"use client"

import { useQuery } from "@tanstack/react-query"
import { Flame, TrendingUp } from "lucide-react"
import { fetchStockDataBatch } from "@/lib/api/stocks"
import type { SectorSlice } from "@/types/agent"

const SECTOR_ETF: Record<string, string> = {
  Technology: "XLK",
  "Consumer Cyclical": "XLY",
  "Consumer Defensive": "XLP",
  Healthcare: "XLV",
  Financial: "XLF",
  "Financial Services": "XLF",
  Energy: "XLE",
  Industrials: "XLI",
  "Basic Materials": "XLB",
  Utilities: "XLU",
  "Real Estate": "XLRE",
  Communication: "XLC",
  "Communication Services": "XLC",
}

interface SectorTrendCardProps {
  sectors: SectorSlice[]
}

export function SectorTrendCard({ sectors }: SectorTrendCardProps) {
  const sectorEtfs = sectors
    .map((s) => ({ sector: s.sector, etf: SECTOR_ETF[s.sector] }))
    .filter((x) => x.etf)

  // Deduplicate ETF symbols (e.g. Financial + Financial Services both map to XLF)
  const etfSymbols = [...new Set(sectorEtfs.map((x) => x.etf))]

  const { data: batchData, isPending: isLoading } = useQuery({
    queryKey: ["sector-etf-batch", etfSymbols.join(",")],
    queryFn: () => fetchStockDataBatch(etfSymbols),
    staleTime: 5 * 60_000,
    enabled: etfSymbols.length > 0,
  })

  if (sectors.length === 0) return null

  return (
    <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-5">
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp size={16} className="text-zinc-500" />
        <h2 className="text-sm font-semibold text-zinc-300 uppercase tracking-wide">
          Sector Trends
        </h2>
      </div>

      {isLoading ? (
        <div className="space-y-2 animate-pulse">
          {sectors.slice(0, 5).map((_, i) => (
            <div key={i} className="h-8 rounded bg-zinc-800" />
          ))}
        </div>
      ) : (
        <div className="space-y-2">
          {sectorEtfs.map(({ sector, etf }) => {
            const data = batchData?.[etf]
            const sectorSlice = sectors.find((s) => s.sector === sector)
            const weight = sectorSlice?.weight_pct ?? 0
            const change = data?.change_percent ?? null
            const isHot = change != null && change > 1

            return (
              <div
                key={sector}
                className="flex items-center justify-between py-2 border-b border-zinc-800/40 last:border-0"
              >
                <div className="flex items-center gap-2">
                  <span className="text-zinc-300 text-sm font-medium">{sector}</span>
                  {isHot && (
                    <span className="inline-flex items-center gap-0.5 text-[10px] font-medium text-amber-400 bg-amber-400/10 px-1.5 py-0.5 rounded">
                      <Flame size={10} />
                      Hot
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-zinc-500 text-xs tabular-nums">
                    {weight.toFixed(1)}% of portfolio
                  </span>
                  <span
                    className={`tabular-nums text-sm font-medium ${
                      change != null
                        ? change >= 0
                          ? "text-green-400"
                          : "text-red-400"
                        : "text-zinc-500"
                    }`}
                  >
                    {change != null
                      ? `${change >= 0 ? "+" : ""}${change.toFixed(2)}%`
                      : "—"}
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
