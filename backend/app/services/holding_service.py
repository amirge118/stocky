import asyncio
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.holding import Holding
from app.schemas.holding import HoldingResponse, PortfolioPosition, PortfolioSummary
from app.services.stock_service import fetch_stock_data_from_yfinance


async def upsert_holding(
    db: AsyncSession,
    symbol: str,
    name: str,
    shares: float,
    price_per_share: float,
) -> HoldingResponse:
    """Insert or update a holding using weighted average cost."""
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
        )
        db.add(holding)
    else:
        new_total_cost = existing.total_cost + shares * price_per_share
        new_shares = existing.shares + shares
        existing.shares = new_shares
        existing.avg_cost = new_total_cost / new_shares
        existing.total_cost = new_total_cost
        existing.name = name
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
        )

    # Fetch live prices concurrently; swallow per-symbol errors
    price_results = await asyncio.gather(
        *[fetch_stock_data_from_yfinance(h.symbol) for h in holdings],
        return_exceptions=True,
    )

    positions: list[PortfolioPosition] = []
    total_value = 0.0
    total_cost = 0.0

    for holding, price_result in zip(holdings, price_results):
        current_price: Optional[float] = None
        current_value: Optional[float] = None
        gain_loss: Optional[float] = None
        gain_loss_pct: Optional[float] = None

        if not isinstance(price_result, Exception):
            current_price = price_result.current_price
            current_value = round(holding.shares * current_price, 2)
            gain_loss = round(current_value - holding.total_cost, 2)
            gain_loss_pct = round((gain_loss / holding.total_cost) * 100, 2) if holding.total_cost else 0.0
            total_value += current_value

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
            )
        )

    # Second pass: compute portfolio_pct
    for pos in positions:
        if pos.current_value is not None and total_value > 0:
            pos.portfolio_pct = round((pos.current_value / total_value) * 100, 2)

    total_gain_loss = round(total_value - total_cost, 2)
    total_gain_loss_pct = round((total_gain_loss / total_cost) * 100, 2) if total_cost else 0.0

    return PortfolioSummary(
        positions=positions,
        total_value=round(total_value, 2),
        total_cost=round(total_cost, 2),
        total_gain_loss=total_gain_loss,
        total_gain_loss_pct=total_gain_loss_pct,
    )
