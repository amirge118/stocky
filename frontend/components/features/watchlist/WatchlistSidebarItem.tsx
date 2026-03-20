"use client"

import { useState, useRef, useEffect } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { deleteWatchlist, renameWatchlist } from "@/lib/api/watchlists"
import { DeleteWatchlistDialog } from "./DeleteWatchlistDialog"
import type { WatchlistListSummary } from "@/types/watchlist"

interface WatchlistSidebarItemProps {
  list: WatchlistListSummary
  isActive: boolean
  onSelect: (id: number) => void
  onDeleted: (id: number) => void
}

export function WatchlistSidebarItem({
  list,
  isActive,
  onSelect,
  onDeleted,
}: WatchlistSidebarItemProps) {
  const queryClient = useQueryClient()
  const [isRenaming, setIsRenaming] = useState(false)
  const [renameValue, setRenameValue] = useState(list.name)
  const [menuOpen, setMenuOpen] = useState(false)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!menuOpen) return
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false)
      }
    }
    document.addEventListener("mousedown", handler)
    return () => document.removeEventListener("mousedown", handler)
  }, [menuOpen])

  const renameMutation = useMutation({
    mutationFn: (name: string) => renameWatchlist(list.id, name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["watchlists"] })
      setIsRenaming(false)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: () => deleteWatchlist(list.id),
    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey: ["watchlists"] })
      const prev = queryClient.getQueryData<WatchlistListSummary[]>(["watchlists"])
      queryClient.setQueryData<WatchlistListSummary[]>(["watchlists"], (old) =>
        old ? old.filter((l) => l.id !== list.id) : []
      )
      return { prev }
    },
    onError: (_err, _vars, ctx) => {
      if (ctx?.prev) queryClient.setQueryData(["watchlists"], ctx.prev)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["watchlists"] })
    },
    onSuccess: () => {
      onDeleted(list.id)
    },
  })

  const commitRename = () => {
    const trimmed = renameValue.trim()
    if (trimmed && trimmed !== list.name) {
      renameMutation.mutate(trimmed)
    } else {
      setIsRenaming(false)
    }
  }

  return (
    <>
      <div
        className={`group flex items-center gap-2 px-3 py-2 rounded-md cursor-pointer select-none transition-colors ${
          isActive ? "bg-zinc-800 text-white" : "text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-200"
        }`}
        onClick={() => !isRenaming && onSelect(list.id)}
      >
        <span className="text-zinc-500 text-xs">★</span>

        {isRenaming ? (
          <input
            autoFocus
            value={renameValue}
            onChange={(e) => setRenameValue(e.target.value)}
            onBlur={commitRename}
            onKeyDown={(e) => {
              if (e.key === "Enter") commitRename()
              if (e.key === "Escape") { setRenameValue(list.name); setIsRenaming(false) }
            }}
            onClick={(e) => e.stopPropagation()}
            className="flex-1 min-w-0 bg-zinc-700 border border-zinc-500 rounded px-1 py-0 text-sm text-white focus:outline-none focus:border-zinc-400"
          />
        ) : (
          <span className="flex-1 min-w-0 text-sm truncate">{list.name}</span>
        )}

        <span className="text-xs text-zinc-600 shrink-0">{list.item_count}</span>

        {/* ··· menu */}
        <div className="relative" ref={menuRef}>
          <button
            onClick={(e) => { e.stopPropagation(); setMenuOpen((v) => !v) }}
            className="opacity-0 group-hover:opacity-100 p-0.5 rounded hover:bg-zinc-700 text-zinc-400 hover:text-zinc-200 text-xs leading-none transition-opacity"
            aria-label="List options"
          >
            ···
          </button>
          {menuOpen && (
            <div className="absolute right-0 top-6 z-20 w-32 bg-zinc-800 border border-zinc-700 rounded shadow-lg py-1">
              <button
                className="w-full text-left px-3 py-1.5 text-sm text-zinc-300 hover:bg-zinc-700 hover:text-white"
                onClick={(e) => { e.stopPropagation(); setMenuOpen(false); setIsRenaming(true); setRenameValue(list.name) }}
              >
                Rename
              </button>
              <button
                className="w-full text-left px-3 py-1.5 text-sm text-red-400 hover:bg-zinc-700 hover:text-red-300"
                onClick={(e) => { e.stopPropagation(); setMenuOpen(false); setDeleteOpen(true) }}
              >
                Delete
              </button>
            </div>
          )}
        </div>
      </div>

      <DeleteWatchlistDialog
        open={deleteOpen}
        listName={list.name}
        onOpenChange={setDeleteOpen}
        onConfirm={() => deleteMutation.mutate()}
      />
    </>
  )
}
