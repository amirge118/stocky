from __future__ import annotations

from datetime import date
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Transaction(BaseModel):
    __tablename__ = "transactions"

    symbol: Mapped[str] = mapped_column(String(15), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(10), nullable=False)  # "BUY" | "SELL"
    shares: Mapped[float] = mapped_column(Float, nullable=False)
    price_per_share: Mapped[float] = mapped_column(Float, nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    realized_gain: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    transaction_date: Mapped[date] = mapped_column(
        sa.Date, nullable=False, server_default=sa.func.current_date()
    )
