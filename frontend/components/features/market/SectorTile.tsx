import type { SectorData } from "@/types/market"

interface SectorTileProps {
  sector: SectorData
  isActive: boolean
  onClick: () => void
}

function getSectorBgClass(pct: number): string {
  if (pct >= 2) return "bg-green-800/60 hover:bg-green-800/80"
  if (pct >= 1) return "bg-green-900/60 hover:bg-green-900/80"
  if (pct > 0) return "bg-green-950/60 hover:bg-green-950/80"
  if (pct === 0) return "bg-zinc-800/60 hover:bg-zinc-800/80"
  if (pct > -1) return "bg-red-950/60 hover:bg-red-950/80"
  if (pct > -2) return "bg-red-900/60 hover:bg-red-900/80"
  return "bg-red-800/60 hover:bg-red-800/80"
}

function getChangeColor(pct: number): string {
  if (pct > 0) return "text-green-400"
  if (pct < 0) return "text-red-400"
  return "text-zinc-400"
}

export function SectorTile({ sector, isActive, onClick }: SectorTileProps) {
  const bgClass = getSectorBgClass(sector.change_percent)
  const changeColor = getChangeColor(sector.change_percent)
  const sign = sector.change_percent >= 0 ? "+" : ""

  return (
    <button
      onClick={onClick}
      className={`
        w-full text-left rounded-lg p-3 border transition-all cursor-pointer
        ${bgClass}
        ${isActive
          ? "border-zinc-500 ring-1 ring-zinc-400"
          : "border-zinc-700/50 hover:border-zinc-600"
        }
      `}
    >
      <div className="flex items-start justify-between gap-1">
        <span className="text-sm font-medium text-white leading-tight">{sector.name}</span>
        <span className={`text-sm font-bold shrink-0 tabular-nums ${changeColor}`}>
          {sign}{sector.change_percent.toFixed(2)}%
        </span>
      </div>
      <div className="text-xs text-zinc-400 mt-1">
        {sector.etf} · ${sector.price.toFixed(2)}
      </div>
    </button>
  )
}
