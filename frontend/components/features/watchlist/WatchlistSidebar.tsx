"use client"

import { useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { createWatchlist } from "@/lib/api/watchlists"
import { WatchlistSidebarItem } from "./WatchlistSidebarItem"
import { NewListInput } from "./NewListInput"
import type { WatchlistListSummary } from "@/types/watchlist"

interface WatchlistSidebarProps {
  lists: WatchlistListSummary[]
  activeListId: number | null
  onSelect: (id: number | null) => void
}

export function WatchlistSidebar({
  lists,
  activeListId,
  onSelect,
}: WatchlistSidebarProps) {
  const queryClient = useQueryClient()
  const [showNewInput, setShowNewInput] = useState(false)
  const totalCount = lists.reduce((acc, l) => acc + l.item_count, 0)

  const createMutation = useMutation({
    mutationFn: (name: string) => createWatchlist({ name }),
    onMutate: async (name) => {
      await queryClient.cancelQueries({ queryKey: ["watchlists"] })
      const prev = queryClient.getQueryData<WatchlistListSummary[]>(["watchlists"])
      const tempId = -Date.now()
      const optimistic: WatchlistListSummary = {
        id: tempId,
        name,
        position: 0,
        item_count: 0,
        created_at: new Date().toISOString(),
      }
      queryClient.setQueryData<WatchlistListSummary[]>(["watchlists"], (old) =>
        old ? [...old, optimistic] : [optimistic]
      )
      return { prev, tempId }
    },
    onError: (_err, _vars, ctx) => {
      if (ctx?.prev) queryClient.setQueryData(["watchlists"], ctx.prev)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["watchlists"] })
    },
    onSuccess: (newList) => {
      onSelect(newList.id)
    },
  })

  return (
    <aside className="w-64 shrink-0 sticky top-[53px] max-h-[calc(100vh-53px)] overflow-y-auto bg-zinc-900 border-r border-zinc-800 flex flex-col py-4">
      {/* All row */}
      <div
        className={`flex items-center gap-2 px-3 py-2 rounded-md mx-2 cursor-pointer select-none transition-colors text-sm ${
          activeListId === null
            ? "bg-zinc-800 text-white"
            : "text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-200"
        }`}
        onClick={() => onSelect(null)}
      >
        <span className="text-zinc-500">≡</span>
        <span className="flex-1 truncate">All</span>
        <span className="text-xs text-zinc-600">{totalCount}</span>
      </div>

      {/* Divider */}
      {lists.length > 0 && <div className="my-2 mx-3 border-t border-zinc-800" />}

      {/* List items */}
      <div className="flex-1 px-2 space-y-0.5">
        {lists.map((list) => (
          <WatchlistSidebarItem
            key={list.id}
            list={list}
            isActive={activeListId === list.id}
            onSelect={onSelect}
            onDeleted={(id) => {
              if (activeListId === id) onSelect(null)
            }}
          />
        ))}

        {/* New list input */}
        {showNewInput && (
          <div className="px-1 py-1">
            <NewListInput
              onCommit={(name) => {
                setShowNewInput(false)
                createMutation.mutate(name)
              }}
              onCancel={() => setShowNewInput(false)}
            />
          </div>
        )}
      </div>

      {/* New list button */}
      <div className="px-3 mt-3">
        <button
          onClick={() => setShowNewInput(true)}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/50 transition-colors"
        >
          <span>+</span>
          <span>New List</span>
        </button>
      </div>
    </aside>
  )
}
