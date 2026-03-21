"""Market overview endpoint."""

from fastapi import APIRouter, HTTPException, status

from app.core.cache import cache_get, cache_set
from app.schemas.market import MarketOverviewResponse
from app.services import market_service

router = APIRouter()


@router.get("/overview", response_model=MarketOverviewResponse, summary="Market overview")
async def get_market_overview() -> MarketOverviewResponse:
    """Return indices, sector heatmap, and top movers. Cached 60 seconds."""
    cache_key = "market:overview"
    try:
        cached = await cache_get(cache_key)
        if cached is not None:
            return MarketOverviewResponse(**cached)
        result = await market_service.get_market_overview()
        await cache_set(cache_key, result.model_dump(), ttl=60)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch market data: {exc}",
        ) from exc
