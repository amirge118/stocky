"use client"

import { useQuery } from "@tanstack/react-query"
import Link from "next/link"
import { ExternalLink, Flame, Newspaper } from "lucide-react"
import { getPortfolioNews } from "@/lib/api/portfolio"
import type { PortfolioNewsItem } from "@/types/portfolio"

const BREAKING_THRESHOLD_MS = 3 * 60 * 60 * 1000 // 3 hours

function timeAgo(ms: number | null): string {
  if (!ms) return ""
  const diff = Date.now() - ms
  const mins = Math.floor(diff / 60_000)
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

function isBreaking(publishedAt: number | null): boolean {
  if (!publishedAt) return false
  return Date.now() - publishedAt < BREAKING_THRESHOLD_MS
}

export function PortfolioNewsFeed() {
  const { data: news, isPending } = useQuery({
    queryKey: ["portfolio-news"],
    queryFn: () => getPortfolioNews(20),
    staleTime: 5 * 60_000,
  })

  return (
    <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-5">
      <div className="flex items-center gap-2 mb-4">
        <Newspaper size={16} className="text-zinc-500" />
        <h2 className="text-sm font-semibold text-zinc-300 uppercase tracking-wide">
          Portfolio News
        </h2>
      </div>

      {isPending ? (
        <div className="space-y-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="animate-pulse flex gap-2">
              <div className="flex-1 space-y-1">
                <div className="h-3 bg-zinc-800 rounded w-full" />
                <div className="h-3 bg-zinc-800 rounded w-4/5" />
              </div>
              <div className="h-3 bg-zinc-800 rounded w-12 shrink-0" />
            </div>
          ))}
        </div>
      ) : !news || news.length === 0 ? (
        <p className="text-zinc-500 text-sm">No news for your holdings.</p>
      ) : (
        <ul className="divide-y divide-zinc-800/70 space-y-0">
          {news.map((item: PortfolioNewsItem, i: number) => {
            const hot = isBreaking(item.published_at)
            return (
              <li key={i} className="py-3 first:pt-0">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <Link
                        href={`/stocks/${item.symbol}`}
                        className="text-xs font-mono font-medium text-blue-400 hover:text-blue-300 shrink-0"
                      >
                        {item.symbol}
                      </Link>
                      {hot && (
                        <span className="inline-flex items-center gap-0.5 text-[10px] font-medium text-amber-400 bg-amber-400/10 px-1.5 py-0.5 rounded">
                          <Flame size={10} />
                          Breaking
                        </span>
                      )}
                    </div>
                    {item.link ? (
                      <a
                        href={item.link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="group/title text-zinc-300 text-sm leading-snug hover:text-white transition-colors line-clamp-2 block mt-0.5"
                      >
                        {item.title}
                      </a>
                    ) : (
                      <p className="text-zinc-300 text-sm leading-snug line-clamp-2 mt-0.5">
                        {item.title}
                      </p>
                    )}
                  </div>
                  {item.link && (
                    <a
                      href={item.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      tabIndex={-1}
                      aria-hidden
                    >
                      <ExternalLink
                        size={12}
                        className="text-zinc-600 hover:text-zinc-400 shrink-0 mt-0.5 transition-colors"
                      />
                    </a>
                  )}
                </div>
                <div className="flex items-center gap-1.5 mt-1 text-[10px] text-zinc-600">
                  {item.publisher && (
                    <span className="truncate max-w-[120px]">{item.publisher}</span>
                  )}
                  {item.published_at && (
                    <>
                      <span>·</span>
                      <span suppressHydrationWarning>
                        {timeAgo(item.published_at)}
                      </span>
                    </>
                  )}
                </div>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
