from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class EarningsEvent(BaseModel):
    """A single earnings event (historical or upcoming)."""

    symbol: str = Field(..., description="Stock ticker symbol")
    earnings_date: date = Field(..., description="Earnings report date")
    eps_estimate: Optional[float] = Field(None, description="Consensus EPS estimate")
    eps_actual: Optional[float] = Field(None, description="Reported EPS")
    surprise_pct: Optional[float] = Field(None, description="EPS surprise percentage")
    revenue_estimate: Optional[float] = Field(
        None, description="Revenue estimate (USD)"
    )
    revenue_actual: Optional[float] = Field(None, description="Reported revenue (USD)")
    is_upcoming: bool = Field(
        False, description="True if earnings date is in the future"
    )
    days_until: Optional[int] = Field(
        None, description="Days until earnings (None if past)"
    )


class EarningsCalendarResponse(BaseModel):
    """Response containing a list of earnings events."""

    items: list[EarningsEvent] = Field(default_factory=list)
