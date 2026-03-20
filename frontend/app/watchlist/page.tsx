"use client"

import { useQuery } from "@tanstack/react-query"
import { useSearchParams, useRouter } from "next/navigation"
import { Suspense } from "react"
import { getWatchlists } from "@/lib/api/watchlists"
import { WatchlistSidebar } from "@/components/features/watchlist/WatchlistSidebar"
import { WatchlistMainPanel } from "@/components/features/watchlist/WatchlistMainPanel"

function WatchlistContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const listParam = searchParams.get("list")
  const activeListId = listParam ? parseInt(listParam, 10) : null

  const { data: lists = [], isError: listsError } = useQuery({
    queryKey: ["watchlists"],
    queryFn: getWatchlists,
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
          <div className="m-6 rounded-xl border border-zinc-800 bg-zinc-900 px-5 py-4 text-sm text-zinc-400">
            Failed to load watchlists. Check your connection and refresh the page.
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
