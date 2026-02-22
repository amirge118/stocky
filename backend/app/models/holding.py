from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Holding(BaseModel):
    __tablename__ = "holdings"

    symbol: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    shares: Mapped[float] = mapped_column(Float, nullable=False)
    avg_cost: Mapped[float] = mapped_column(Float, nullable=False)
    total_cost: Mapped[float] = mapped_column(Float, nullable=False)
