from datetime import date

import sqlalchemy as sa
from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Holding(BaseModel):
    __tablename__ = "holdings"

    symbol: Mapped[str] = mapped_column(String(15), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    shares: Mapped[float] = mapped_column(Float, nullable=False)
    avg_cost: Mapped[float] = mapped_column(Float, nullable=False)
    total_cost: Mapped[float] = mapped_column(Float, nullable=False)
    purchase_date: Mapped[date] = mapped_column(
        sa.Date, nullable=False, server_default=sa.func.current_date()
    )
