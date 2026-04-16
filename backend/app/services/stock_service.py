"""Stock CRUD, sector peers, and re-exports for backward compatibility."""

import asyncio
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stock import Stock
from app.schemas.stock import (
    SectorPeerResponse,
    StockCreate,
    StockDataResponse,
    StockInfoResponse,
    StockUpdate,
)
from app.services.stock_ai import generate_ai_analysis, generate_compare_summary
from app.services.stock_data import (
    fetch_stock_data_batch,
    fetch_stock_data_from_yfinance,
    fetch_stock_dividends,
    fetch_stock_enriched_batch,
    fetch_stock_history,
    fetch_stock_info,
    fetch_stock_news,
    search_stocks_from_yfinance,
)

__all__ = [
    "generate_ai_analysis",
    "generate_compare_summary",
    "fetch_stock_data_batch",
    "fetch_stock_data_from_yfinance",
    "fetch_stock_dividends",
    "fetch_stock_enriched_batch",
    "fetch_stock_history",
    "fetch_stock_info",
    "fetch_stock_news",
    "search_stocks_from_yfinance",
]


async def get_stock_by_symbol(db: AsyncSession, symbol: str) -> Optional[Stock]:
    """Get a stock by its symbol."""
    result = await db.execute(
        select(Stock).where(Stock.symbol == symbol.upper())
    )
    return result.scalar_one_or_none()


async def get_stocks(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    sector: Optional[str] = None,
) -> tuple[list[Stock], int]:
    """Get list of stocks with pagination. Optional sector filter."""
    filt = select(Stock)
    if sector and sector.strip():
        filt = filt.where(func.lower(Stock.sector) == sector.strip().lower())
    if sector and sector.strip():
        count_stmt = select(func.count(Stock.id)).where(
            func.lower(Stock.sector) == sector.strip().lower()
        )
    else:
        count_stmt = select(func.count(Stock.id))
    total = (await db.execute(count_stmt)).scalar() or 0
    result = await db.execute(filt.offset(skip).limit(limit).order_by(Stock.symbol))
    stocks = result.scalars().all()
    return list(stocks), total


async def create_stock(db: AsyncSession, stock_data: StockCreate) -> Stock:
    """Create a new stock."""
    existing = await get_stock_by_symbol(db, stock_data.symbol)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Stock with symbol {stock_data.symbol} already exists",
        )

    stock = Stock(
        symbol=stock_data.symbol.upper(),
        name=stock_data.name,
        exchange=stock_data.exchange,
        sector=stock_data.sector,
    )
    db.add(stock)
    await db.commit()
    await db.refresh(stock)
    return stock


async def update_stock(
    db: AsyncSession,
    symbol: str,
    stock_data: StockUpdate,
) -> Optional[Stock]:
    """Update a stock."""
    stock = await get_stock_by_symbol(db, symbol)
    if not stock:
        return None

    update_data = stock_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(stock, key, value)

    await db.commit()
    await db.refresh(stock)
    return stock


async def delete_stock(db: AsyncSession, symbol: str) -> bool:
    """Delete a stock."""
    stock = await get_stock_by_symbol(db, symbol)
    if not stock:
        return False

    await db.delete(stock)
    await db.commit()
    return True


async def get_sector_list(db: AsyncSession) -> list[str]:
    """Curated GICS sectors (stable display order) merged with any extra DB sectors."""
    from app.core.sector_universe import SECTOR_DISPLAY_ORDER

    result = await db.execute(
        select(Stock.sector).where(Stock.sector.isnot(None)).distinct()
    )
    db_sectors = {row[0] for row in result.all() if row[0]}
    ordered: list[str] = []
    seen: set[str] = set()
    for s in SECTOR_DISPLAY_ORDER:
        ordered.append(s)
        seen.add(s.lower())
    for s in sorted(db_sectors):
        if s.lower() not in seen:
            ordered.append(s)
    return ordered


async def get_sector_browse_results(
    db: AsyncSession,
    sector: str,
    limit: int = 30,
) -> list[SectorPeerResponse]:
    """Return enriched stocks for sector browsing.

    Merges curated SECTOR_UNIVERSE symbols with DB stocks for the same sector,
    then enriches via fetch_stock_data_batch + fetch_stock_info (both cached).
    """
    from app.core.sector_universe import get_symbols_for_sector

    curated = get_symbols_for_sector(sector, limit)
    db_stocks_result, _ = await get_stocks(db, skip=0, limit=50, sector=sector)
    db_syms = [s.symbol for s in db_stocks_result if s.symbol not in curated]
    symbol_order = (curated + db_syms)[:limit]

    if not symbol_order:
        return []

    # Gracefully degrade: if price batch fails (e.g. cold-start rate limit),
    # still return the symbol list with null prices rather than a 500.
    try:
        batch = await fetch_stock_data_batch(symbol_order)
    except Exception:
        batch = {}

    infos = await asyncio.gather(
        *[fetch_stock_info(s) for s in symbol_order],
        return_exceptions=True,
    )

    db_meta = {s.symbol: s for s in db_stocks_result}
    out: list[SectorPeerResponse] = []
    for sym, info_res in zip(symbol_order, infos):
        data = batch.get(sym)
        info: Optional[StockInfoResponse] = (
            info_res if isinstance(info_res, StockInfoResponse) else None
        )
        meta = db_meta.get(sym)
        out.append(
            SectorPeerResponse(
                symbol=sym,
                name=(
                    (meta.name if meta else None)
                    or (data.name if data else None)
                    or sym
                ),
                sector=(info.sector if info else None) or sector,
                industry=info.industry if info else None,
                current_price=data.current_price if data else None,
                day_change_percent=data.change_percent if data else None,
                pe_ratio=info.pe_ratio if info else None,
                market_cap=info.market_cap if info else None,
                is_current=False,
            )
        )
    return out


async def get_sector_peers(
    db: AsyncSession,
    sector: str,
    current_symbol: Optional[str] = None,
    limit: int = 10,
) -> list[SectorPeerResponse]:
    """Get stocks in the same sector with enriched price and fundamentals."""
    if not sector or not sector.strip():
        return []
    stocks, _ = await get_stocks(db, skip=0, limit=limit + 20, sector=sector.strip())
    current = (current_symbol or "").upper()
    peers = [s for s in stocks if s.symbol == current]
    others = [s for s in stocks if s.symbol != current][: limit - (1 if peers else 0)]
    peers = peers + others

    async def _enrich(stock: Stock) -> SectorPeerResponse:
        data_res, info_res = await asyncio.gather(
            fetch_stock_data_from_yfinance(stock.symbol),
            fetch_stock_info(stock.symbol),
            return_exceptions=True,
        )
        data: Optional[StockDataResponse] = data_res if isinstance(data_res, StockDataResponse) else None
        info: Optional[StockInfoResponse] = info_res if isinstance(info_res, StockInfoResponse) else None
        return SectorPeerResponse(
            symbol=stock.symbol,
            name=stock.name,
            sector=info.sector if info is not None else stock.sector,
            industry=info.industry if info is not None else None,
            current_price=data.current_price if data is not None else None,
            day_change_percent=data.change_percent if data is not None else None,
            pe_ratio=info.pe_ratio if info is not None else None,
            market_cap=info.market_cap if info is not None else None,
            is_current=stock.symbol == current,
        )

    results = await asyncio.gather(*[_enrich(p) for p in peers])
    return list(results)
