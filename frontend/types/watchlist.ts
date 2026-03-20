export interface WatchlistListSummary {
  id: number
  name: string
  position: number
  item_count: number
  created_at: string
}

export interface WatchlistItem {
  id: number
  watchlist_id: number
  symbol: string
  name: string
  exchange: string
  sector: string | null
  position: number
  created_at: string
}

export interface WatchlistListResponse {
  id: number
  name: string
  position: number
  created_at: string
  items: WatchlistItem[]
}

export interface WatchlistListCreate {
  name: string
}

export interface WatchlistItemAdd {
  symbol: string
  name: string
  exchange: string
  sector?: string | null
}
