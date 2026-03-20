import asyncio
from datetime import date, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.holding import Holding
from app.schemas.agent import SectorBreakdownResponse, SectorSlice
from app.schemas.holding import (
    HoldingResponse,
    PortfolioHistoryPoint,
    PortfolioHistoryResponse,
    PortfolioPosition,
    PortfolioSummary,
)
from app.schemas.stock import (
    PortfolioNewsItem,
    StockDataResponse,
    StockInfoResponse,
)
from app.services.stock_data import (
    fetch_stock_data_from_yfinance,
    fetch_stock_info,
    fetch_stock_news,
)
from app.services.yfinance_service import fetch_history_daily, fetch_history_intraday


async def upsert_holding(
    db: AsyncSession,
    symbol: str,
    name: str,
    shares: float,
    price_per_share: float,
    purchase_date: Optional[date] = None,
) -> HoldingResponse:
    """Insert or update a holding using weighted average cost.

    purchase_date is only set on initial insert; subsequent updates preserve
    the original entry date.
    """
    sym = symbol.upper()
    result = await db.execute(select(Holding).where(Holding.symbol == sym))
    existing = result.scalar_one_or_none()

    if existing is None:
        holding = Holding(
            symbol=sym,
            name=name,
            shares=shares,
            avg_cost=price_per_share,
            total_cost=shares * price_per_share,
            purchase_date=purchase_date or date.today(),
        )
        db.add(holding)
    else:
        new_total_cost = existing.total_cost + shares * price_per_share
        new_shares = existing.shares + shares
        existing.shares = new_shares
        existing.avg_cost = new_total_cost / new_shares
        existing.total_cost = new_total_cost
        existing.name = name
        # Do NOT overwrite purchase_date on update
        holding = existing

    await db.commit()
    await db.refresh(holding)
    return HoldingResponse.model_validate(holding)


async def delete_holding(db: AsyncSession, symbol: str) -> bool:
    """Delete a holding by symbol. Returns False if not found."""
    sym = symbol.upper()
    result = await db.execute(select(Holding).where(Holding.symbol == sym))
    holding = result.scalar_one_or_none()
    if holding is None:
        return False
    await db.delete(holding)
    await db.commit()
    return True


async def get_portfolio(db: AsyncSession) -> PortfolioSummary:
    """Fetch all holdings and enrich them with live prices."""
    result = await db.execute(select(Holding).order_by(Holding.symbol))
    holdings = list(result.scalars().all())

    if not holdings:
        return PortfolioSummary(
            positions=[],
            total_value=0.0,
            total_cost=0.0,
            total_gain_loss=0.0,
            total_gain_loss_pct=0.0,
            total_day_change=None,
            total_day_change_pct=None,
        )

    # Fetch live prices concurrently; swallow per-symbol errors
    price_results = await asyncio.gather(
        *[fetch_stock_data_from_yfinance(h.symbol) for h in holdings],
        return_exceptions=True,
    )

    positions: list[PortfolioPosition] = []
    total_value = 0.0
    total_cost = 0.0
    total_day_change = 0.0

    for holding, price_result in zip(holdings, price_results):
        current_price: Optional[float] = None
        current_value: Optional[float] = None
        gain_loss: Optional[float] = None
        gain_loss_pct: Optional[float] = None
        day_change: Optional[float] = None
        day_change_percent: Optional[float] = None

        if isinstance(price_result, StockDataResponse):
            resp: StockDataResponse = price_result
            current_price = resp.current_price
            current_value = round(holding.shares * current_price, 2)
            gain_loss = round(current_value - holding.total_cost, 2)
            gain_loss_pct = round((gain_loss / holding.total_cost) * 100, 2) if holding.total_cost else 0.0
            day_change = round(holding.shares * resp.change, 2)
            day_change_percent = resp.change_percent
            total_value += current_value
            total_day_change += day_change

        total_cost += holding.total_cost

        positions.append(
            PortfolioPosition(
                symbol=holding.symbol,
                name=holding.name,
                shares=holding.shares,
                avg_cost=round(holding.avg_cost, 4),
                total_cost=round(holding.total_cost, 2),
                current_price=current_price,
                current_value=current_value,
                gain_loss=gain_loss,
                gain_loss_pct=gain_loss_pct,
                portfolio_pct=None,  # filled in second pass
                day_change=day_change,
                day_change_percent=day_change_percent,
            )
        )

    # Second pass: compute portfolio_pct
    for pos in positions:
        if pos.current_value is not None and total_value > 0:
            pos.portfolio_pct = round((pos.current_value / total_value) * 100, 2)

    total_gain_loss = round(total_value - total_cost, 2)
    total_gain_loss_pct = round((total_gain_loss / total_cost) * 100, 2) if total_cost else 0.0
    total_day_change_pct = (
        round((total_day_change / total_value) * 100, 2) if total_value > 0 else None
    )

    return PortfolioSummary(
        positions=positions,
        total_value=round(total_value, 2),
        total_cost=round(total_cost, 2),
        total_gain_loss=total_gain_loss,
        total_gain_loss_pct=total_gain_loss_pct,
        total_day_change=round(total_day_change, 2),
        total_day_change_pct=total_day_change_pct,
    )


async def get_sector_breakdown(
    db: AsyncSession,
    portfolio: Optional[PortfolioSummary] = None,
) -> SectorBreakdownResponse:
    """Group portfolio holdings by sector with value and weight.
    Uses fetch_stock_info (cached 10min) for sector instead of raw yfinance."""
    if portfolio is None:
        portfolio = await get_portfolio(db)
    positions = portfolio.positions
    total_value = portfolio.total_value or 0.0

    if not positions:
        return SectorBreakdownResponse(sectors=[], total_value=0.0)

    # Use fetch_stock_info (cached 10min) instead of raw yfinance - includes sector
    info_results = await asyncio.gather(
        *[fetch_stock_info(pos.symbol) for pos in positions],
        return_exceptions=True,
    )
    sectors = [
        info.sector if isinstance(info, StockInfoResponse) else None
        for info in info_results
    ]

    # Group by sector
    sector_map: dict[str, dict] = {}
    for pos, sector in zip(positions, sectors):
        sector_name = sector or "Unknown"
        val = pos.current_value or 0.0
        if sector_name not in sector_map:
            sector_map[sector_name] = {"total_value": 0.0, "symbols": []}
        sector_map[sector_name]["total_value"] += val
        sector_map[sector_name]["symbols"].append(pos.symbol)

    slices: list[SectorSlice] = []
    for sec_name, data in sector_map.items():
        weight = round(data["total_value"] / total_value * 100, 2) if total_value > 0 else 0.0
        slices.append(
            SectorSlice(
                sector=sec_name,
                total_value=round(data["total_value"], 2),
                weight_pct=weight,
                symbols=data["symbols"],
                num_holdings=len(data["symbols"]),
            )
        )

    slices.sort(key=lambda s: s.weight_pct, reverse=True)
    return SectorBreakdownResponse(sectors=slices, total_value=round(total_value, 2))


async def get_portfolio_summary(db: AsyncSession) -> tuple[PortfolioSummary, SectorBreakdownResponse]:
    """Fetch portfolio and sector breakdown in one pass (avoids duplicate get_portfolio)."""
    portfolio = await get_portfolio(db)
    sector_breakdown = await get_sector_breakdown(db, portfolio=portfolio)
    return portfolio, sector_breakdown


async def get_portfolio_news(db: AsyncSession, limit: int = 20) -> list[PortfolioNewsItem]:
    """Fetch and merge news for all portfolio holdings, sorted by date (newest first)."""
    result = await db.execute(select(Holding).order_by(Holding.symbol))
    holdings = list(result.scalars().all())
    if not holdings:
        return []

    news_tasks = [fetch_stock_news(h.symbol, limit=5) for h in holdings]
    news_results = await asyncio.gather(*news_tasks, return_exceptions=True)

    seen_titles: set[str] = set()
    merged: list[PortfolioNewsItem] = []
    for holding, news_list in zip(holdings, news_results):
        if not isinstance(news_list, list):
            continue
        for item in news_list:
            key = (item.title or "").strip().lower()
            if key and key not in seen_titles:
                seen_titles.add(key)
                merged.append(
                    PortfolioNewsItem(
                        symbol=holding.symbol,
                        title=item.title,
                        publisher=item.publisher,
                        link=item.link,
                        published_at=item.published_at,
                    )
                )

    merged.sort(
        key=lambda x: x.published_at or 0,
        reverse=True,
    )
    return merged[:limit]


async def get_portfolio_history(db: AsyncSession, period: str = "1m") -> PortfolioHistoryResponse:
    """Compute portfolio $ value over time using yfinance historical prices.

    For the "1d" period we use intraday (5-min) bars.
    For all other periods we use daily closes, respecting each holding's
    purchase_date so a holding only contributes value from the day it was bought.
    """
    from collections import defaultdict

    result = await db.execute(select(Holding).order_by(Holding.symbol))
    holdings = list(result.scalars().all())
    if not holdings:
        return PortfolioHistoryResponse(period=period, data=[])

    # ── Intraday branch (1D) ────────────────────────────────────────────────
    if period == "1d":
        intraday_results = await asyncio.gather(
            *[fetch_history_intraday(h.symbol) for h in holdings],
            return_exceptions=True,
        )
        ts_values: dict[int, float] = defaultdict(float)
        for holding, bars in zip(holdings, intraday_results):
            if not isinstance(bars, list):
                continue
            for dt, price in bars:
                ts_ms = int(dt.timestamp() * 1000)
                ts_values[ts_ms] += holding.shares * price

        if not ts_values:
            return PortfolioHistoryResponse(period=period, data=[])

        points = [
            PortfolioHistoryPoint(t=t, value=round(v, 2))
            for t, v in sorted(ts_values.items())
        ]
        return PortfolioHistoryResponse(period=period, data=points)

    # ── Daily branch ────────────────────────────────────────────────────────
    today = date.today()
    period_map: dict[str, date] = {
        "1w": today - timedelta(days=7),
        "1m": today - timedelta(days=30),
        "6m": today - timedelta(days=180),
        "1y": today - timedelta(days=365),
    }

    if period == "all":
        window_start = min(h.purchase_date for h in holdings)
    else:
        window_start = period_map.get(period, today - timedelta(days=30))

    daily_results = await asyncio.gather(
        *[fetch_history_daily(h.symbol, window_start, today) for h in holdings],
        return_exceptions=True,
    )

    date_values: dict[date, float] = defaultdict(float)
    for holding, prices in zip(holdings, daily_results):
        if not isinstance(prices, dict):
            continue
        for d, price in prices.items():
            # Only count this holding from its purchase_date onward
            if d >= holding.purchase_date:
                date_values[d] += holding.shares * price

    if not date_values:
        return PortfolioHistoryResponse(period=period, data=[])

    import calendar

    points = [
        PortfolioHistoryPoint(
            t=int(calendar.timegm(d.timetuple()) * 1000),
            value=round(v, 2),
        )
        for d, v in sorted(date_values.items())
    ]
    return PortfolioHistoryResponse(period=period, data=points)
