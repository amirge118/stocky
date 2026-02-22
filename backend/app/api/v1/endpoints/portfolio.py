from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.holding import HoldingCreate, PortfolioPosition, PortfolioSummary
from app.services import holding_service

router = APIRouter()


@router.get("", response_model=PortfolioSummary)
async def get_portfolio(db: AsyncSession = Depends(get_db)) -> PortfolioSummary:
    """Return all holdings with live prices and P&L."""
    return await holding_service.get_portfolio(db)


@router.post("", response_model=PortfolioPosition, status_code=status.HTTP_201_CREATED)
async def add_holding(
    data: HoldingCreate,
    db: AsyncSession = Depends(get_db),
) -> PortfolioPosition:
    """Add shares to a position (or create it). Returns the enriched position."""
    holding = await holding_service.upsert_holding(
        db,
        symbol=data.symbol,
        name=data.name,
        shares=data.shares,
        price_per_share=data.price_per_share,
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
    )


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
