"use client"

import { useQuery } from "@tanstack/react-query"
import { ExternalLink } from "lucide-react"
import { getStockNews } from "@/lib/api/stocks"

function timeAgo(ms: number | null): string {
  if (!ms) return ""
  const diff = Date.now() - ms
  const mins = Math.floor(diff / 60_000)
  if (mins < 60) return `${mins}m`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h`
  return `${Math.floor(hrs / 24)}d`
}

interface StockNewsProps {
  symbol: string
}

export function StockNews({ symbol }: StockNewsProps) {
  const { data: news, isPending } = useQuery({
    queryKey: ["news", symbol],
    queryFn: () => getStockNews(symbol),
    staleTime: 5 * 60_000,
  })

  return (
    <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-4">
      <h2 className="text-xs font-semibold text-zinc-400 uppercase tracking-wide mb-3">Latest News</h2>

      {isPending ? (
        <div className="space-y-2.5">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="animate-pulse flex gap-2">
              <div className="flex-1 space-y-1">
                <div className="h-3 bg-zinc-800 rounded w-full" />
                <div className="h-3 bg-zinc-800 rounded w-4/5" />
              </div>
              <div className="h-3 bg-zinc-800 rounded w-6 shrink-0" />
            </div>
          ))}
        </div>
      ) : !news || news.length === 0 ? (
        <p className="text-zinc-500 text-xs">No news available.</p>
      ) : (
        <ul className="divide-y divide-zinc-800/70">
          {news.slice(0, 6).map((item, i) => (
            <li key={i} className="py-2 first:pt-0 last:pb-0">
              {item.link ? (
                <a
                  href={item.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="group flex items-start justify-between gap-2"
                >
                  <span className="text-zinc-300 text-xs leading-snug group-hover:text-white transition-colors line-clamp-2">
                    {item.title}
                  </span>
                  <ExternalLink
                    size={10}
                    className="text-zinc-600 group-hover:text-zinc-400 shrink-0 mt-0.5 transition-colors"
                  />
                </a>
              ) : (
                <p className="text-zinc-300 text-xs leading-snug line-clamp-2">{item.title}</p>
              )}
              <div className="flex items-center gap-1.5 mt-0.5 text-[10px] text-zinc-600">
                {item.publisher && <span className="truncate max-w-[120px]">{item.publisher}</span>}
                {item.published_at && (
                  <>
                    <span>·</span>
                    <span suppressHydrationWarning>{timeAgo(item.published_at)}</span>
                  </>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
