import { del, get, post, put } from "./client"
import type {
  WatchlistItem,
  WatchlistItemAdd,
  WatchlistListCreate,
  WatchlistListResponse,
  WatchlistListSummary,
} from "@/types/watchlist"

export async function getWatchlists(): Promise<WatchlistListSummary[]> {
  return get<WatchlistListSummary[]>("/api/v1/watchlists")
}

export async function createWatchlist(
  data: WatchlistListCreate
): Promise<WatchlistListResponse> {
  return post<WatchlistListResponse>("/api/v1/watchlists", data)
}

export async function getWatchlist(listId: number): Promise<WatchlistListResponse> {
  return get<WatchlistListResponse>(`/api/v1/watchlists/${listId}`)
}

export async function renameWatchlist(
  listId: number,
  name: string
): Promise<WatchlistListResponse> {
  return put<WatchlistListResponse>(`/api/v1/watchlists/${listId}`, { name })
}

export async function deleteWatchlist(listId: number): Promise<void> {
  await del(`/api/v1/watchlists/${listId}`)
}

export async function addItemToWatchlist(
  listId: number,
  data: WatchlistItemAdd
): Promise<WatchlistItem> {
  return post<WatchlistItem>(`/api/v1/watchlists/${listId}/items`, data)
}

export async function removeItemFromWatchlist(
  listId: number,
  symbol: string
): Promise<void> {
  await del(`/api/v1/watchlists/${listId}/items/${symbol}`)
}
