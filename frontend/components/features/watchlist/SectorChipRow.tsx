"use client"

import { getSectorActiveColor, getSectorIcon, getSectorIconColor } from "@/lib/sector-icons"

interface SectorChipRowProps {
  sectors: string[]
  active: string | null
  onSelect: (sector: string) => void
  loading?: boolean
}

export function SectorChipRow({ sectors, active, onSelect, loading }: SectorChipRowProps) {
  if (loading) {
    return (
      <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-none">
        {Array.from({ length: 7 }).map((_, i) => (
          <div
            key={i}
            className="h-9 rounded-full bg-zinc-800 animate-pulse shrink-0"
            style={{ width: `${80 + (i % 3) * 20}px` }}
          />
        ))}
      </div>
    )
  }

  return (
    <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-none -mx-1 px-1">
      {sectors.map((sector) => {
        const Icon = getSectorIcon(sector)
        const isActive = active === sector
        const activeClasses = getSectorActiveColor(sector)
        const iconColor = getSectorIconColor(sector)

        return (
          <button
            key={sector}
            type="button"
            onClick={() => onSelect(sector)}
            aria-pressed={isActive}
            className={[
              "shrink-0 inline-flex items-center gap-1.5 h-9 px-3 rounded-full",
              "text-xs font-medium border transition-all duration-200",
              isActive
                ? `${activeClasses} shadow-sm`
                : "bg-zinc-800/80 border-zinc-700 text-zinc-300 hover:bg-zinc-700 hover:border-zinc-600 hover:text-zinc-100",
            ].join(" ")}
          >
            <Icon className={`w-3.5 h-3.5 shrink-0 ${isActive ? "" : iconColor}`} />
            <span className="whitespace-nowrap">{sector}</span>
          </button>
        )
      })}
    </div>
  )
}
