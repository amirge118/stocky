"use client"

import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
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

interface SectorAllocationChartProps {
  sectors: SectorSlice[]
}

export function SectorAllocationChart({ sectors }: SectorAllocationChartProps) {
  if (!sectors.length) return null

  const data = sectors.map((s) => ({
    ...s,
    name: s.sector,
    value: s.weight_pct,
  }))

  return (
    <ResponsiveContainer width="100%" height={280}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={70}
          outerRadius={110}
          paddingAngle={2}
          dataKey="value"
          nameKey="name"
        >
          {data.map((_, index) => (
            <Cell key={index} fill={SECTOR_COLORS[index % SECTOR_COLORS.length]} />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
        <Legend
          formatter={(value) => (
            <span className="text-xs text-zinc-400">{value}</span>
          )}
        />
      </PieChart>
    </ResponsiveContainer>
  )
}
