"use client"

import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
} from "recharts"
import type { SectorSlice } from "@/types/agent"
import { SECTOR_COLORS } from "@/lib/constants/colors"

interface TooltipPayload {
  name: string
  value: number
  payload: SectorSlice & { color: string }
}

function CustomTooltip({
  active,
  payload,
}: {
  active?: boolean
  payload?: TooltipPayload[]
}) {
  if (!active || !payload?.length) return null
  const d = payload[0]
  return (
    <div className="bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-xs shadow-xl">
      <p className="font-semibold text-white mb-1">{d.name}</p>
      <p className="text-zinc-400">
        ${d.payload.total_value.toLocaleString("en-US", { maximumFractionDigits: 0 })}
      </p>
      <p className="text-zinc-400">{d.payload.weight_pct.toFixed(1)}%</p>
    </div>
  )
}

function fmtCompact(n: number): string {
  if (Math.abs(n) >= 1_000_000)
    return `$${(n / 1_000_000).toFixed(2)}M`
  if (Math.abs(n) >= 1_000)
    return `$${(n / 1_000).toFixed(1)}K`
  return `$${n.toFixed(0)}`
}

interface SectorAllocationChartProps {
  sectors: SectorSlice[]
  totalValue?: number
}

export function SectorAllocationChart({ sectors, totalValue }: SectorAllocationChartProps) {
  if (!sectors.length) return null

  const data = sectors.map((s) => ({
    ...s,
    name: s.sector,
    value: s.weight_pct,
  }))

  return (
    <div className="relative">
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={80}
            outerRadius={120}
            paddingAngle={2}
            dataKey="value"
            nameKey="name"
            stroke="none"
          >
            {data.map((_, index) => (
              <Cell key={index} fill={SECTOR_COLORS[index % SECTOR_COLORS.length]} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
        </PieChart>
      </ResponsiveContainer>
      {totalValue != null && (
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <span className="text-2xl font-bold text-white tabular-nums">
            {fmtCompact(totalValue)}
          </span>
          <span className="text-[11px] text-zinc-500 uppercase tracking-wider mt-0.5">
            Total Value
          </span>
        </div>
      )}
    </div>
  )
}
