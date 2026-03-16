"""Pydantic schemas for market overview data."""

from pydantic import BaseModel


class IndexData(BaseModel):
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    sparkline: list[float]


class SectorNewsItem(BaseModel):
    title: str
    url: str | None = None
    publisher: str | None = None


class SectorData(BaseModel):
    name: str
    etf: str
    price: float
    change_percent: float
    news: list[SectorNewsItem]


class MoverData(BaseModel):
    symbol: str
    name: str
    price: float
    change_percent: float


class MarketOverviewResponse(BaseModel):
    indices: list[IndexData]
    sectors: list[SectorData]
    gainers: list[MoverData]
    losers: list[MoverData]
    updated_at: str
