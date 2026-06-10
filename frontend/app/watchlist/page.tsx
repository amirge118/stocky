"use client"

import { useQuery } from "@tanstack/react-query"
import { useSearchParams, useRouter } from "next/navigation"
import { Suspense } from "react"
import { getWatchlists } from "@/lib/api/watchlists"
import { ApiError } from "@/lib/api/client"
import { WatchlistSidebar } from "@/components/features/watchlist/WatchlistSidebar"
import { WatchlistMainPanel } from "@/components/features/watchlist/WatchlistMainPanel"

function WatchlistContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const listParam = searchParams.get("list")
  const activeListId = listParam ? parseInt(listParam, 10) : null

  const { data: lists = [], isError: listsError, error: listsErr } = useQuery({
    queryKey: ["watchlists"],
    queryFn: getWatchlists,
    retry: (failureCount, error) => {
      if (error instanceof ApiError && error.status === 503) return failureCount < 5
      return failureCount < 2
    },
    retryDelay: (attempt) => Math.min(2000 * 2 ** attempt, 30_000),
  })

  const setActiveListId = (id: number | null) => {
    if (id === null) {
      router.push("/watchlist")
    } else {
      router.push(`/watchlist?list=${id}`)
    }
  }

  return (
    <div className="flex min-h-[calc(100vh-53px)]">
      <WatchlistSidebar
        lists={lists}
        activeListId={activeListId}
        onSelect={setActiveListId}
      />
      <div className="flex-1 flex flex-col min-w-0">
        {listsError && (
          <div className="m-6 rounded-xl border border-amber-800/50 bg-amber-950/30 px-5 py-4 text-sm text-amber-300">
            {listsErr instanceof ApiError && listsErr.status === 503
              ? "Server is waking up — watchlists will load in a few seconds. Try refreshing."
              : "Failed to load watchlists. Check your connection and refresh the page."}
          </div>
        )}
        <WatchlistMainPanel activeListId={activeListId} />
      </div>
    </div>
  )
}

export default function WatchlistPage() {
  return (
    <Suspense>
      <WatchlistContent />
    </Suspense>
  )
}
