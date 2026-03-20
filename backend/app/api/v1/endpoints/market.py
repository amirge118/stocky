"""Market overview endpoint."""

from fastapi import APIRouter, HTTPException, status

from app.schemas.market import MarketOverviewResponse
from app.services import market_service

router = APIRouter()


@router.get("/overview", response_model=MarketOverviewResponse, summary="Market overview")
async def get_market_overview() -> MarketOverviewResponse:
    """Return indices, sector heatmap, and top movers. Cached 5 minutes."""
    try:
        return await market_service.get_market_overview()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch market data: {exc}",
        ) from exc
