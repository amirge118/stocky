from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.agent import SectorBreakdownResponse


class HoldingCreate(BaseModel):
    symbol: str
    name: str
    shares: float
    price_per_share: float


class HoldingResponse(BaseModel):
    id: int
    symbol: str
    name: str
    shares: float
    avg_cost: float
    total_cost: float
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class PortfolioPosition(BaseModel):
    symbol: str
    name: str
    shares: float
    avg_cost: float
    total_cost: float
    current_price: Optional[float]
    current_value: Optional[float]
    gain_loss: Optional[float]
    gain_loss_pct: Optional[float]
    portfolio_pct: Optional[float]
    day_change: Optional[float] = None
    day_change_percent: Optional[float] = None


class PortfolioSummary(BaseModel):
    positions: list[PortfolioPosition]
    total_value: float
    total_cost: float
    total_gain_loss: float
    total_gain_loss_pct: float
    total_day_change: Optional[float] = None
    total_day_change_pct: Optional[float] = None


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
