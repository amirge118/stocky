from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.watchlist import WatchlistItem, WatchlistList
from app.schemas.watchlist import WatchlistListSummary


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
