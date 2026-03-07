"use client"

import type { SectorSlice } from "@/types/agent"
import { SECTOR_COLORS } from "@/lib/constants/colors"

interface SectorBreakdownTableProps {
  sectors: SectorSlice[]
}

export function SectorBreakdownTable({ sectors }: SectorBreakdownTableProps) {
  if (!sectors.length) return null

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-[10px] font-semibold uppercase tracking-widest text-zinc-500 border-b border-zinc-800">
            <th className="text-left pb-2 pr-4">Sector</th>
            <th className="text-right pb-2 pr-4">Holdings</th>
            <th className="text-right pb-2 pr-4">Value</th>
            <th className="text-right pb-2">Weight</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-800/50">
          {sectors.map((s, i) => (
            <tr key={s.sector} className="hover:bg-zinc-800/30 transition-colors">
              <td className="py-3 pr-4">
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className="w-2.5 h-2.5 rounded-full shrink-0"
                    style={{ backgroundColor: SECTOR_COLORS[i % SECTOR_COLORS.length] }}
                  />
                  <span className="text-zinc-200 font-medium">{s.sector}</span>
                </div>
                <div className="flex flex-wrap gap-1 pl-4">
                  {s.symbols.map((sym) => (
                    <span
                      key={sym}
                      className="text-[10px] font-mono text-zinc-500 bg-zinc-800/80 px-1.5 py-0.5 rounded"
                    >
                      {sym}
                    </span>
                  ))}
                </div>
              </td>
              <td className="py-3 pr-4 text-right text-zinc-400 align-top">{s.num_holdings}</td>
              <td className="py-3 pr-4 text-right text-zinc-300 align-top">
                ${s.total_value.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </td>
              <td className="py-3 text-right align-top">
                <div className="flex items-center justify-end gap-2">
                  <div className="w-16 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: `${Math.min(s.weight_pct, 100)}%`,
                        backgroundColor: SECTOR_COLORS[i % SECTOR_COLORS.length],
                      }}
                    />
                  </div>
                  <span className="text-zinc-300 w-10 text-right">{s.weight_pct.toFixed(1)}%</span>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
