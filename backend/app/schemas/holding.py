from datetime import datetime
from typing import Optional

from pydantic import BaseModel


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


class PortfolioSummary(BaseModel):
    positions: list[PortfolioPosition]
    total_value: float
    total_cost: float
    total_gain_loss: float
    total_gain_loss_pct: float
