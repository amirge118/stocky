from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.agent import SectorBreakdownResponse


class HoldingCreate(BaseModel):
    symbol: str
    name: str
    shares: float
    price_per_share: float
    purchase_date: date | None = None


class HoldingResponse(BaseModel):
    id: int
    symbol: str
    name: str
    shares: float
    avg_cost: float
    total_cost: float
    purchase_date: date
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True


class PortfolioPosition(BaseModel):
    symbol: str
    name: str
    shares: float
    avg_cost: float
    total_cost: float
    current_price: float | None
    current_value: float | None
    gain_loss: float | None
    gain_loss_pct: float | None
    portfolio_pct: float | None
    day_change: float | None = None
    day_change_percent: float | None = None
    purchase_date: date | None = None


class PortfolioSummary(BaseModel):
    positions: list[PortfolioPosition]
    total_value: float
    total_cost: float
    total_gain_loss: float
    total_gain_loss_pct: float
    total_day_change: float | None = None
    total_day_change_pct: float | None = None


class PortfolioSummaryWithSector(BaseModel):
    """Combined portfolio + sector breakdown in one response to avoid duplicate fetches."""

    portfolio: PortfolioSummary
    sector_breakdown: SectorBreakdownResponse


class PortfolioHistoryPoint(BaseModel):
    t: int  # Unix ms
    value: float


class PortfolioHistoryResponse(BaseModel):
    period: str
    data: list[PortfolioHistoryPoint]
