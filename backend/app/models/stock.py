from typing import Optional

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Stock(BaseModel):
    """Stock model for storing stock information."""

    __tablename__ = "stocks"

    symbol: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    exchange: Mapped[str] = mapped_column(String(50), nullable=False)
    sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    __table_args__ = (
        Index("idx_stocks_symbol", "symbol"),
        Index("idx_stocks_exchange", "exchange"),
    )
