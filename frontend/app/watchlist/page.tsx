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

  const { data: lists = [] } = useQuery({
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
      <WatchlistMainPanel activeListId={activeListId} />
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
