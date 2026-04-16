from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class WatchlistItemResponse(BaseModel):
    id: int
    watchlist_id: int
    symbol: str
    name: str
    exchange: str
    sector: Optional[str]
    position: int
    created_at: datetime

    model_config = {"from_attributes": True}


class WatchlistListSummary(BaseModel):
    id: int
    name: str
    position: int
    item_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class WatchlistListResponse(BaseModel):
    id: int
    name: str
    position: int
    created_at: datetime
    items: list[WatchlistItemResponse] = []

    model_config = {"from_attributes": True}


class WatchlistListCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class WatchlistListUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class WatchlistItemAdd(BaseModel):
    symbol: str = Field(..., max_length=15)
    name: str = Field(..., max_length=255)
    exchange: str = Field(..., max_length=50)
    sector: Optional[str] = Field(None, max_length=100)


class MomentumSignal(BaseModel):
    symbol: str
    z_score: float
    direction: str  # "up" | "down"
    last_return_pct: float


class WatchlistMomentumResponse(BaseModel):
    signals: list[MomentumSignal]


class WatchlistItemBulkAdd(BaseModel):
    items: list[WatchlistItemAdd] = Field(..., min_length=1, max_length=50)


class WatchlistBulkAddResult(BaseModel):
    added: list[WatchlistItemResponse] = []
    skipped: list[str] = []   # symbols already in the list (duplicate)
    failed: list[dict] = []   # [{"symbol": "...", "error": "..."}]
