from typing import Optional

from sqlalchemy import ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class WatchlistList(BaseModel):
    """A named watchlist."""

    __tablename__ = "watchlist_lists"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    items: Mapped[list["WatchlistItem"]] = relationship(
        "WatchlistItem",
        back_populates="watchlist",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="WatchlistItem.position",
    )

    __table_args__ = (Index("idx_watchlist_lists_position", "position"),)


class WatchlistItem(BaseModel):
    """A stock entry inside a watchlist."""

    __tablename__ = "watchlist_items"

    watchlist_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("watchlist_lists.id", ondelete="CASCADE"),
        nullable=False,
    )
    symbol: Mapped[str] = mapped_column(String(15), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    exchange: Mapped[str] = mapped_column(String(50), nullable=False)
    sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    watchlist: Mapped["WatchlistList"] = relationship(
        "WatchlistList", back_populates="items"
    )

    __table_args__ = (
        UniqueConstraint("watchlist_id", "symbol", name="uq_watchlist_item"),
        Index("idx_watchlist_items_watchlist_id", "watchlist_id"),
        Index("idx_watchlist_items_symbol", "symbol"),
    )
