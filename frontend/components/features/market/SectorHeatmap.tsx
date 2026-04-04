"use client"

import { useState } from "react"
import { SectorTile } from "./SectorTile"
import { SectorNewsPanel } from "./SectorNewsPanel"
import type { SectorData } from "@/types/market"

interface SectorHeatmapProps {
  sectors: SectorData[]
}

export function SectorHeatmap({ sectors }: SectorHeatmapProps) {
  const [activeSector, setActiveSector] = useState<string | null>(null)

  const handleTileClick = (name: string) => {
    setActiveSector((prev) => (prev === name ? null : name))
  }

  const activeSectorData = sectors.find((s) => s.name === activeSector)

  if (sectors.length === 0) {
    return (
      <section>
        <h2 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-3">
          Sector Heatmap
        </h2>
        <p className="text-sm text-zinc-500 rounded-lg border border-zinc-800 bg-zinc-900/50 px-4 py-6 text-center">
          Sector ETF tiles are not configured for this deployment. Benchmarks and top movers still
          reflect broad market tone.
        </p>
      </section>
    )
  }

  return (
    <section>
      <h2 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-3">
        Sector Heatmap
      </h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
        {sectors.map((sector) => (
          <SectorTile
            key={sector.name}
            sector={sector}
            isActive={activeSector === sector.name}
            onClick={() => handleTileClick(sector.name)}
          />
        ))}
      </div>
      {activeSectorData && <SectorNewsPanel sector={activeSectorData} />}
    </section>
  )
}
