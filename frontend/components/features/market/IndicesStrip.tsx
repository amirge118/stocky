import { IndexCard } from "./IndexCard"
import type { IndexData } from "@/types/market"

interface IndicesStripProps {
  indices: IndexData[]
}

export function IndicesStrip({ indices }: IndicesStripProps) {
  return (
    <section>
      <h2 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-3">
        Indices
      </h2>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {indices.map((index) => (
          <IndexCard key={index.symbol} index={index} />
        ))}
      </div>
    </section>
  )
}
