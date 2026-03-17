import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ConditionType(str, enum.Enum):
    ABOVE = "ABOVE"
    BELOW = "BELOW"
    EQUAL = "EQUAL"


class Alert(BaseModel):
    """Price alert for a stock ticker."""

    __tablename__ = "alerts"

    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    condition_type: Mapped[ConditionType] = mapped_column(
        Enum(ConditionType, name="conditiontype"), nullable=False
    )
    target_price: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    last_triggered: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (Index("idx_alerts_ticker_is_active", "ticker", "is_active"),)
