import type { SectorData } from "@/types/market"

interface SectorNewsPanelProps {
  sector: SectorData
}

export function SectorNewsPanel({ sector }: SectorNewsPanelProps) {
  if (sector.news.length === 0) {
    return (
      <div className="mt-3 px-4 py-3 bg-zinc-900 border border-zinc-700 rounded-lg text-sm text-zinc-500">
        No recent news for {sector.name}.
      </div>
    )
  }

  return (
    <div className="mt-3 px-4 py-3 bg-zinc-900 border border-zinc-700 rounded-lg space-y-2">
      <p className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
        {sector.name} News
      </p>
      {sector.news.map((item, i) => (
        <div key={i} className="flex gap-2">
          <span className="text-zinc-600 text-sm">•</span>
          {item.url ? (
            <a
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-zinc-300 hover:text-white hover:underline line-clamp-2 transition-colors"
            >
              {item.title}
              {item.publisher && (
                <span className="text-zinc-500 ml-1">— {item.publisher}</span>
              )}
            </a>
          ) : (
            <span className="text-sm text-zinc-300 line-clamp-2">
              {item.title}
              {item.publisher && (
                <span className="text-zinc-500 ml-1">— {item.publisher}</span>
              )}
            </span>
          )}
        </div>
      ))}
    </div>
  )
}
