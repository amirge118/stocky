from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.limiter import limiter
from app.schemas.holding import (
    HoldingCreate,
    PortfolioPosition,
    PortfolioSummary,
    PortfolioSummaryWithSector,
)
from app.schemas.sector_breakdown import SectorBreakdownResponse
from app.schemas.stock import PortfolioNewsItem
from app.services import holding_service

router = APIRouter()


@router.get("", response_model=PortfolioSummary)
async def get_portfolio(db: AsyncSession = Depends(get_db)) -> PortfolioSummary:
    """Return all holdings with live prices and P&L."""
    return await holding_service.get_portfolio(db)


@router.get("/summary", response_model=PortfolioSummaryWithSector)
async def get_portfolio_summary(db: AsyncSession = Depends(get_db)) -> PortfolioSummaryWithSector:
    """Return portfolio and sector breakdown in one request (avoids duplicate fetches)."""
    portfolio, sector_breakdown = await holding_service.get_portfolio_summary(db)
    return PortfolioSummaryWithSector(portfolio=portfolio, sector_breakdown=sector_breakdown)


@router.post("", response_model=PortfolioPosition, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def add_holding(
    request: Request,
    data: HoldingCreate,
    db: AsyncSession = Depends(get_db),
) -> PortfolioPosition:
    """Add shares to a position (or create it). Returns the enriched position."""
    from datetime import date

    holding = await holding_service.upsert_holding(
        db,
        symbol=data.symbol,
        name=data.name,
        shares=data.shares,
        price_per_share=data.price_per_share,
        purchase_date=data.purchase_date or date.today(),
    )

    # Return a lightweight PortfolioPosition without live price lookup
    return PortfolioPosition(
        symbol=holding.symbol,
        name=holding.name,
        shares=holding.shares,
        avg_cost=holding.avg_cost,
        total_cost=holding.total_cost,
        current_price=None,
        current_value=None,
        gain_loss=None,
        gain_loss_pct=None,
        portfolio_pct=None,
        purchase_date=holding.purchase_date,
    )


@router.get("/news", response_model=list[PortfolioNewsItem])
async def get_portfolio_news(
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> list[PortfolioNewsItem]:
    """Fetch unified news feed for all portfolio holdings."""
    return await holding_service.get_portfolio_news(db, limit=limit)


@router.delete("/{symbol}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_holding(
    symbol: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove an entire position."""
    deleted = await holding_service.delete_holding(db, symbol)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No holding found for symbol {symbol.upper()}",
        )


@router.get("/sector-breakdown", response_model=SectorBreakdownResponse)
async def get_sector_breakdown(db: AsyncSession = Depends(get_db)) -> SectorBreakdownResponse:
    """Return portfolio holdings grouped by sector with value and weight."""
    return await holding_service.get_sector_breakdown(db)
