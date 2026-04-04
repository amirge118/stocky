"use client"

import { useQuery } from "@tanstack/react-query"
import { Flame } from "lucide-react"
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
    <div>
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 animate-pulse">
          {sectors.slice(0, 4).map((_, i) => (
            <div key={i} className="h-16 rounded-xl bg-zinc-800/40" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {sectorEtfs.map(({ sector, etf }) => {
            const data = batchData?.[etf]
            const sectorSlice = sectors.find((s) => s.sector === sector)
            const weight = sectorSlice?.weight_pct ?? 0
            const change = data?.change_percent ?? null
            const isHot = change != null && Math.abs(change) > 1

            return (
              <div
                key={sector}
                className="flex items-center justify-between p-3 rounded-xl bg-zinc-800/40 border border-zinc-800/60"
              >
                <div>
                  <div className="flex items-center gap-1.5">
                    <span className="text-sm text-zinc-200 font-medium">{sector}</span>
                    {isHot && (
                      <span className="inline-flex items-center gap-0.5 text-[10px] font-medium text-amber-400 bg-amber-400/10 px-1.5 py-0.5 rounded">
                        <Flame size={10} />
                        Hot
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-1.5 mt-0.5">
                    <span className="text-[10px] font-mono text-zinc-600">{etf}</span>
                    <span className="text-[10px] text-zinc-600">&middot; {weight.toFixed(1)}% of portfolio</span>
                  </div>
                </div>
                <span
                  className={`text-lg font-bold font-mono tabular-nums ${
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
            )
          })}
        </div>
      )}
    </div>
  )
}
