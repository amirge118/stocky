"use client"

import type { SectorSlice } from "@/types/portfolio"
import { SECTOR_COLORS } from "@/lib/constants/colors"

interface SectorBreakdownTableProps {
  sectors: SectorSlice[]
}

function fmtValue(n: number): string {
  if (Math.abs(n) >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`
  if (Math.abs(n) >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return n.toFixed(0)
}

export function SectorBreakdownTable({ sectors }: SectorBreakdownTableProps) {
  if (!sectors.length) return null

  return (
    <div className="space-y-1">
      {sectors.map((s, i) => {
        const color = SECTOR_COLORS[i % SECTOR_COLORS.length]
        return (
          <div key={s.sector} className="py-3">
            <div className="flex items-center gap-3">
              <span
                className="w-3 h-3 rounded-full shrink-0"
                style={{ backgroundColor: color }}
              />
              <div className="flex-1 min-w-0">
                <div className="flex justify-between items-baseline mb-1.5">
                  <span className="text-sm font-medium text-zinc-200">{s.sector}</span>
                  <span className="text-sm font-mono text-zinc-300 tabular-nums">
                    {s.weight_pct.toFixed(1)}%
                  </span>
                </div>
                <div className="h-2 rounded-full bg-zinc-800 overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{ width: `${Math.min(s.weight_pct, 100)}%`, backgroundColor: color }}
                  />
                </div>
                <div className="flex flex-wrap gap-1 mt-1.5">
                  {s.symbols.map((sym) => (
                    <span
                      key={sym}
                      className="text-[10px] font-mono text-zinc-500 bg-zinc-800 px-1.5 py-0.5 rounded"
                    >
                      {sym}
                    </span>
                  ))}
                </div>
              </div>
              <span className="text-xs text-zinc-500 font-mono w-20 text-right tabular-nums shrink-0">
                ${fmtValue(s.total_value)}
              </span>
            </div>
          </div>
        )
      })}
    </div>
  )
}
