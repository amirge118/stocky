"use client"

import { useMemo, useRef, useEffect, useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Layers, Search } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { getSectors, getStocksBySector, searchStocks, type SectorPeer } from "@/lib/api/stocks"
import { addItemToWatchlist, bulkAddToWatchlist } from "@/lib/api/watchlists"
import { useToast } from "@/hooks/use-toast"
import { Sparkline } from "@/components/features/stocks/Sparkline"
import { SectorChipRow } from "./SectorChipRow"
import { SectorStockList } from "./SectorStockList"
import type { StockSearchResult } from "@/types/stock"
import type {
  WatchlistItem,
  WatchlistItemAdd,
  WatchlistListResponse,
  WatchlistListSummary,
} from "@/types/watchlist"

type Mode = "search" | "browse"

interface WatchlistAddStockDialogProps {
  open: boolean
  listId: number
  listName: string
  onOpenChange: (open: boolean) => void
}

export function WatchlistAddStockDialog({
  open,
  listId,
  listName,
  onOpenChange,
}: WatchlistAddStockDialogProps) {
  const { toast } = useToast()
  const queryClient = useQueryClient()

  // ── Search mode state ──────────────────────────────────────────────────────
  const [mode, setMode] = useState<Mode>("search")
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<StockSearchResult[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [searchError, setSearchError] = useState<string | null>(null)
  const [rowErrors, setRowErrors] = useState<Record<string, string>>({})
  const [addingSymbol, setAddingSymbol] = useState<string | null>(null)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // ── Browse mode state ──────────────────────────────────────────────────────
  const [activeSector, setActiveSector] = useState<string | null>(null)
  const [sectorFilter, setSectorFilter] = useState("")
  const [selectedSymbols, setSelectedSymbols] = useState<Set<string>>(new Set())
  const [bulkAdding, setBulkAdding] = useState(false)

  // ── Reset on close ─────────────────────────────────────────────────────────
  useEffect(() => {
    if (!open) {
      setMode("search")
      setQuery("")
      setResults([])
      setIsSearching(false)
      setSearchError(null)
      setRowErrors({})
      setAddingSymbol(null)
      setActiveSector(null)
      setSectorFilter("")
      setSelectedSymbols(new Set())
      setBulkAdding(false)
    }
  }, [open])

  // ── Search debounce ────────────────────────────────────────────────────────
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    if (query.trim().length < 1) { setResults([]); setIsSearching(false); return }
    setIsSearching(true)
    setSearchError(null)
    debounceRef.current = setTimeout(async () => {
      try {
        const data = await searchStocks(query.trim())
        setResults(data)
      } catch (err) {
        setResults([])
        setSearchError(err instanceof Error ? err.message : "Search failed")
      } finally {
        setIsSearching(false)
      }
    }, 400)
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current) }
  }, [query])

  // ── Browse: sectors query (lazy) ───────────────────────────────────────────
  const { data: sectors = [], isPending: sectorsLoading } = useQuery({
    queryKey: ["sectors"],
    queryFn: getSectors,
    staleTime: 30 * 60_000,
    enabled: mode === "browse",
  })

  // ── Browse: sector stocks query (lazy) ────────────────────────────────────
  const { data: sectorStocks = [], isPending: sectorStocksLoading } = useQuery({
    queryKey: ["stocks-by-sector", activeSector],
    queryFn: () => getStocksBySector(activeSector!, 30),
    staleTime: 5 * 60_000,
    enabled: mode === "browse" && !!activeSector,
  })

  // ── Already-in-list symbols (from cache, zero extra network) ──────────────
  const existingItems =
    queryClient.getQueryData<WatchlistListResponse>(["watchlists", listId])?.items ?? []
  const existingSymbols = useMemo(
    () => new Set(existingItems.map((i) => i.symbol)),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [existingItems.length]
  )

  // ── Filtered sector stocks ─────────────────────────────────────────────────
  const filteredSectorStocks = useMemo(() => {
    const q = sectorFilter.trim().toLowerCase()
    if (!q) return sectorStocks
    return sectorStocks.filter(
      (s) =>
        s.symbol.toLowerCase().includes(q) || s.name.toLowerCase().includes(q)
    )
  }, [sectorStocks, sectorFilter])

  // ── Single-add mutation (search mode) ─────────────────────────────────────
  const mutation = useMutation({
    mutationFn: (result: StockSearchResult) =>
      addItemToWatchlist(listId, {
        symbol: result.symbol,
        name: result.name,
        exchange: result.exchange,
        sector: result.sector ?? null,
      }),
    onMutate: async (result) => {
      await queryClient.cancelQueries({ queryKey: ["watchlists", listId] })
      const prev = queryClient.getQueryData<WatchlistListResponse>(["watchlists", listId])
      const optimistic: WatchlistItem = {
        id: -Date.now(),
        watchlist_id: listId,
        symbol: result.symbol,
        name: result.name,
        exchange: result.exchange,
        sector: result.sector ?? null,
        position: 0,
        created_at: new Date().toISOString(),
      }
      queryClient.setQueryData<WatchlistListResponse>(["watchlists", listId], (old) =>
        old ? { ...old, items: [...old.items, optimistic] } : old
      )
      queryClient.setQueryData<WatchlistListSummary[]>(
        ["watchlists"],
        (old) =>
          old?.map((l) =>
            l.id === listId ? { ...l, item_count: l.item_count + 1 } : l
          )
      )
      return { prev }
    },
    onError: (error: Error, result, ctx) => {
      if (ctx?.prev) queryClient.setQueryData(["watchlists", listId], ctx.prev)
      queryClient.invalidateQueries({ queryKey: ["watchlists"] })
      setRowErrors((prev) => ({ ...prev, [result.symbol]: error.message || "Failed to add" }))
      setAddingSymbol(null)
    },
    onSuccess: (_item, result) => {
      toast({ title: `${result.symbol} added to ${listName}` })
      setAddingSymbol(null)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["watchlists", listId] })
      queryClient.invalidateQueries({ queryKey: ["watchlists"] })
    },
  })

  const handleAdd = (result: StockSearchResult) => {
    setRowErrors((prev) => { const next = { ...prev }; delete next[result.symbol]; return next })
    setAddingSymbol(result.symbol)
    mutation.mutate(result)
  }

  // ── Single-add from Browse (reuses search-mode mutation via cast) ──────────
  const handleAddFromBrowse = (peer: SectorPeer) => {
    setRowErrors((prev) => { const next = { ...prev }; delete next[peer.symbol]; return next })
    setAddingSymbol(peer.symbol)
    // Cast to StockSearchResult shape — mutation only uses symbol/name/exchange/sector
    mutation.mutate({
      symbol: peer.symbol,
      name: peer.name,
      exchange: "NASDAQ",
      sector: peer.sector ?? activeSector ?? null,
      industry: peer.industry ?? null,
      current_price: peer.current_price ?? null,
      currency: null,
      country: null,
      sparkline: null,
    } as unknown as StockSearchResult)
  }

  // ── Bulk-add mutation ──────────────────────────────────────────────────────
  const bulkMutation = useMutation({
    mutationFn: (items: WatchlistItemAdd[]) => bulkAddToWatchlist(listId, items),
    onMutate: async (items) => {
      await queryClient.cancelQueries({ queryKey: ["watchlists", listId] })
      const prev = queryClient.getQueryData<WatchlistListResponse>(["watchlists", listId])
      queryClient.setQueryData<WatchlistListResponse>(["watchlists", listId], (old) => {
        if (!old) return old
        const newItems = items.map((it, idx) => ({
          id: -Date.now() - idx,
          watchlist_id: listId,
          symbol: it.symbol,
          name: it.name,
          exchange: it.exchange,
          sector: it.sector ?? null,
          position: old.items.length + idx,
          created_at: new Date().toISOString(),
        }))
        return { ...old, items: [...old.items, ...newItems] }
      })
      queryClient.setQueryData<WatchlistListSummary[]>(["watchlists"], (old) =>
        old?.map((l) =>
          l.id === listId ? { ...l, item_count: l.item_count + items.length } : l
        )
      )
      return { prev }
    },
    onError: (err: Error, _items, ctx) => {
      if (ctx?.prev) queryClient.setQueryData(["watchlists", listId], ctx.prev)
      queryClient.invalidateQueries({ queryKey: ["watchlists"] })
      toast({ title: "Bulk add failed", description: err.message, variant: "destructive" })
      setBulkAdding(false)
    },
    onSuccess: (result) => {
      const n = result.added.length
      const s = result.skipped.length
      toast({
        title: `Added ${n} stock${n === 1 ? "" : "s"} to ${listName}`,
        description: s > 0 ? `${s} already in list` : undefined,
      })
      setSelectedSymbols(new Set())
      setBulkAdding(false)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["watchlists", listId] })
      queryClient.invalidateQueries({ queryKey: ["watchlists"] })
    },
  })

  const handleBulkAdd = (peers: SectorPeer[]) => {
    const items: WatchlistItemAdd[] = peers.map((p) => ({
      symbol: p.symbol,
      name: p.name,
      exchange: "NASDAQ",
      sector: p.sector ?? activeSector ?? undefined,
    }))
    if (items.length === 0) return
    setBulkAdding(true)
    bulkMutation.mutate(items)
  }

  const toggleSymbol = (sym: string) =>
    setSelectedSymbols((prev) => {
      const next = new Set(prev)
      if (next.has(sym)) next.delete(sym)
      else next.add(sym)
      return next
    })

  const showSkeleton = isSearching
  const showEmpty =
    !isSearching && !searchError && query.trim().length > 0 && results.length === 0

  const addableCount = filteredSectorStocks.filter((s) => !existingSymbols.has(s.symbol)).length

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className={[
          "bg-zinc-900 border-zinc-700 transition-all duration-200",
          mode === "browse" ? "sm:max-w-2xl" : "sm:max-w-[620px]",
        ].join(" ")}
      >
        <DialogHeader>
          <DialogTitle className="text-white">Add to {listName}</DialogTitle>
        </DialogHeader>

        {/* Mode toggle */}
        <div className="flex gap-1 p-1 rounded-lg bg-zinc-800/80 border border-zinc-700 w-fit">
          {(["search", "browse"] as Mode[]).map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => setMode(m)}
              className={[
                "px-3 py-1.5 text-xs font-medium rounded-md transition-all duration-150",
                mode === m
                  ? "bg-zinc-700 text-white shadow-sm"
                  : "text-zinc-400 hover:text-zinc-200",
              ].join(" ")}
            >
              {m === "search" ? "Search" : "Browse by Sector"}
            </button>
          ))}
        </div>

        {/* ── Search mode ──────────────────────────────────────────────────── */}
        {mode === "search" && (
          <>
            <div className="relative">
              <Input
                autoFocus
                placeholder="Search by ticker or company name..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="pr-10 bg-zinc-800 border-zinc-600 text-white placeholder:text-zinc-400 focus-visible:ring-zinc-500"
              />
              <span className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 pointer-events-none text-sm">
                🔍
              </span>
            </div>

            <div className="min-h-[120px] max-h-[380px] overflow-y-auto">
              {showSkeleton && (
                <div className="space-y-2 mt-2">
                  {[0, 1, 2].map((i) => (
                    <div key={i} className="h-16 rounded-md bg-zinc-800 animate-pulse" />
                  ))}
                </div>
              )}

              {searchError && (
                <p className="text-sm text-amber-400 text-center py-8">{searchError}</p>
              )}

              {showEmpty && (
                <p className="text-sm text-zinc-400 text-center py-8">
                  No results found for &ldquo;{query}&rdquo;
                </p>
              )}

              {!isSearching && results.length > 0 && (
                <ul className="divide-y divide-zinc-700 mt-2 rounded-md border border-zinc-700 overflow-hidden">
                  {results.map((result) => {
                    const isUp =
                      result.sparkline && result.sparkline.length >= 2
                        ? result.sparkline[result.sparkline.length - 1] >= result.sparkline[0]
                        : true

                    return (
                      <li
                        key={result.symbol}
                        className="flex items-center gap-4 px-4 py-3 bg-zinc-900 hover:bg-zinc-800 transition-colors"
                      >
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <Badge
                              variant="outline"
                              className="font-mono text-xs shrink-0 border-zinc-600 text-zinc-200"
                            >
                              {result.symbol}
                            </Badge>
                            <span className="font-medium text-sm text-white truncate">
                              {result.name}
                            </span>
                            <span className="text-xs text-zinc-400 shrink-0">
                              {result.exchange}
                            </span>
                          </div>
                          <div className="flex items-center gap-1 mt-0.5 text-xs text-zinc-500">
                            {result.sector && <span>{result.sector}</span>}
                            {result.sector && result.industry && <span>·</span>}
                            {result.industry && <span>{result.industry}</span>}
                          </div>
                          {rowErrors[result.symbol] && (
                            <p className="text-xs text-red-400 mt-0.5">{rowErrors[result.symbol]}</p>
                          )}
                        </div>

                        {result.sparkline && result.sparkline.length >= 2 ? (
                          <Sparkline data={result.sparkline} />
                        ) : (
                          <div className="w-[72px] shrink-0" />
                        )}

                        <div className="flex items-center gap-3 shrink-0">
                          <div className="text-right">
                            {result.current_price != null ? (
                              <span
                                className={`text-sm font-mono tabular-nums font-semibold ${
                                  isUp ? "text-green-400" : "text-red-400"
                                }`}
                              >
                                ${result.current_price.toFixed(2)}
                              </span>
                            ) : (
                              <span className="text-sm text-zinc-500">—</span>
                            )}
                          </div>
                          <Button
                            size="sm"
                            onClick={() => handleAdd(result)}
                            disabled={addingSymbol === result.symbol}
                            className="bg-zinc-700 hover:bg-zinc-600 text-white border-0"
                          >
                            {addingSymbol === result.symbol ? "Adding…" : "Add"}
                          </Button>
                        </div>
                      </li>
                    )
                  })}
                </ul>
              )}
            </div>
          </>
        )}

        {/* ── Browse mode ──────────────────────────────────────────────────── */}
        {mode === "browse" && (
          <>
            <SectorChipRow
              sectors={sectors}
              active={activeSector}
              onSelect={setActiveSector}
              loading={sectorsLoading}
            />

            {activeSector && (
              <div className="flex items-center gap-2 mt-1">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-zinc-500 pointer-events-none" />
                  <Input
                    placeholder={`Filter ${activeSector}…`}
                    value={sectorFilter}
                    onChange={(e) => setSectorFilter(e.target.value)}
                    className="pl-8 h-9 bg-zinc-800 border-zinc-600 text-white text-sm placeholder:text-zinc-500 focus-visible:ring-zinc-500"
                  />
                </div>
                {selectedSymbols.size > 0 && (
                  <Button
                    size="sm"
                    disabled={bulkAdding}
                    onClick={() =>
                      handleBulkAdd(
                        filteredSectorStocks.filter((s) => selectedSymbols.has(s.symbol))
                      )
                    }
                    className="bg-blue-600 hover:bg-blue-500 text-white border-0 whitespace-nowrap text-xs shrink-0"
                  >
                    {bulkAdding ? "Adding…" : `Add Selected (${selectedSymbols.size})`}
                  </Button>
                )}
                <Button
                  size="sm"
                  variant="outline"
                  disabled={bulkAdding || addableCount === 0}
                  onClick={() =>
                    handleBulkAdd(
                      filteredSectorStocks.filter((s) => !existingSymbols.has(s.symbol))
                    )
                  }
                  className="border-zinc-600 text-zinc-300 hover:bg-zinc-800 hover:text-white whitespace-nowrap text-xs shrink-0"
                >
                  Add All{addableCount > 0 ? ` (${addableCount})` : ""}
                </Button>
              </div>
            )}

            <div className="min-h-[200px] max-h-[360px] overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-zinc-700 scrollbar-track-transparent">
              {!activeSector ? (
                <div className="flex flex-col items-center justify-center h-full py-12 text-zinc-500">
                  <div className="w-12 h-12 rounded-full bg-zinc-800 flex items-center justify-center mb-3">
                    <Layers className="w-5 h-5 text-zinc-500" />
                  </div>
                  <p className="text-sm font-medium text-zinc-400">Pick a sector to browse stocks</p>
                  <p className="text-xs text-zinc-600 mt-1">
                    Choose from Technology, Healthcare, ETFs, and more
                  </p>
                </div>
              ) : (
                <SectorStockList
                  stocks={filteredSectorStocks}
                  existingSymbols={existingSymbols}
                  selected={selectedSymbols}
                  onToggleSelect={toggleSymbol}
                  onAddSingle={handleAddFromBrowse}
                  addingSymbol={addingSymbol}
                  rowErrors={rowErrors}
                  loading={sectorStocksLoading}
                />
              )}
            </div>
          </>
        )}

        <div className="flex justify-end pt-1">
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            className="border-zinc-600 text-zinc-300 hover:bg-zinc-800 hover:text-white"
          >
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
