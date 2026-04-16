import asyncio
import math
from datetime import date, timedelta
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.watchlist import WatchlistItem, WatchlistList
from app.schemas.watchlist import MomentumSignal, WatchlistListSummary
from app.services.yfinance_service import fetch_history_daily


async def get_all_lists(db: AsyncSession) -> list[WatchlistListSummary]:
    """Return all watchlists with item counts."""
    count_sub = (
        select(
            WatchlistItem.watchlist_id,
            func.count(WatchlistItem.id).label("item_count"),
        )
        .group_by(WatchlistItem.watchlist_id)
        .subquery()
    )

    stmt = (
        select(
            WatchlistList.id,
            WatchlistList.name,
            WatchlistList.position,
            WatchlistList.created_at,
            func.coalesce(count_sub.c.item_count, 0).label("item_count"),
        )
        .outerjoin(count_sub, WatchlistList.id == count_sub.c.watchlist_id)
        .order_by(WatchlistList.position, WatchlistList.id)
    )

    result = await db.execute(stmt)
    rows = result.all()
    return [
        WatchlistListSummary(
            id=row.id,
            name=row.name,
            position=row.position,
            created_at=row.created_at,
            item_count=row.item_count,
        )
        for row in rows
    ]


async def create_list(db: AsyncSession, name: str) -> WatchlistList:
    wl = WatchlistList(name=name)
    db.add(wl)
    await db.commit()
    await db.refresh(wl)
    return wl


async def get_list(db: AsyncSession, list_id: int) -> Optional[WatchlistList]:
    result = await db.execute(
        select(WatchlistList).where(WatchlistList.id == list_id)
    )
    return result.scalars().first()


async def rename_list(
    db: AsyncSession, list_id: int, name: str
) -> Optional[WatchlistList]:
    wl = await get_list(db, list_id)
    if not wl:
        return None
    wl.name = name
    await db.commit()
    await db.refresh(wl)
    return wl


async def delete_list(db: AsyncSession, list_id: int) -> bool:
    wl = await get_list(db, list_id)
    if not wl:
        return False
    await db.delete(wl)
    await db.commit()
    return True


async def add_item(
    db: AsyncSession,
    list_id: int,
    symbol: str,
    name: str,
    exchange: str,
    sector: Optional[str],
) -> WatchlistItem:
    item = WatchlistItem(
        watchlist_id=list_id,
        symbol=symbol.upper(),
        name=name,
        exchange=exchange,
        sector=sector,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def compute_momentum_signals(symbols: list[str]) -> list[MomentumSignal]:
    """Return symbols with statistically unusual daily returns (|Z-score| >= 2.0).

    Uses 90 days of historical closes. Requires at least 30 closes per symbol.
    Symbols with insufficient data or zero variance are silently excluded.
    """
    if not symbols:
        return []

    end = date.today()
    start = end - timedelta(days=90)

    histories = await asyncio.gather(
        *[fetch_history_daily(sym, start, end) for sym in symbols],
        return_exceptions=True,
    )

    results: list[MomentumSignal] = []

    for sym, hist in zip(symbols, histories):
        if not isinstance(hist, dict) or not hist:
            continue

        closes = sorted(hist.items())  # list of (date, price)
        prices = [price for _, price in closes]

        if len(prices) < 31:  # need at least 31 closes to get 30 returns
            continue

        returns = [(prices[i] - prices[i - 1]) / prices[i - 1] for i in range(1, len(prices))]
        n = len(returns)
        mean = sum(returns) / n
        variance = sum((r - mean) ** 2 for r in returns) / n
        sigma = math.sqrt(variance)

        if sigma < 1e-9:
            continue

        last_return = returns[-1]
        z = (last_return - mean) / sigma

        if abs(z) >= 2.0:
            results.append(
                MomentumSignal(
                    symbol=sym,
                    z_score=round(z, 2),
                    direction="up" if last_return >= 0 else "down",
                    last_return_pct=round(last_return * 100, 2),
                )
            )

    return results


async def add_items_bulk(
    db: AsyncSession,
    list_id: int,
    items: list[dict],
) -> tuple[list[WatchlistItem], list[str], list[dict]]:
    """Best-effort bulk add. Per-item commits so a single duplicate doesn't abort the batch.

    Returns (added, skipped, failed) where:
    - added  — successfully inserted WatchlistItem records
    - skipped — symbols that were already in the list (IntegrityError)
    - failed  — symbols that failed for other reasons, with error messages
    """
    added: list[WatchlistItem] = []
    skipped: list[str] = []
    failed: list[dict] = []
    for it in items:
        try:
            record = WatchlistItem(
                watchlist_id=list_id,
                symbol=it["symbol"].upper(),
                name=it["name"],
                exchange=it.get("exchange", "NASDAQ"),
                sector=it.get("sector"),
            )
            db.add(record)
            await db.commit()
            await db.refresh(record)
            added.append(record)
        except IntegrityError:
            await db.rollback()
            skipped.append(it["symbol"].upper())
        except Exception as exc:  # noqa: BLE001
            await db.rollback()
            failed.append({"symbol": it["symbol"].upper(), "error": str(exc)})
    return added, skipped, failed


async def remove_item(db: AsyncSession, list_id: int, symbol: str) -> bool:
    result = await db.execute(
        select(WatchlistItem).where(
            WatchlistItem.watchlist_id == list_id,
            WatchlistItem.symbol == symbol.upper(),
        )
    )
    item = result.scalars().first()
    if not item:
        return False
    await db.delete(item)
    await db.commit()
    return True
