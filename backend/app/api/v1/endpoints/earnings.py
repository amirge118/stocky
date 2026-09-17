from fastapi import APIRouter, Query

from app.schemas.earnings import EarningsCalendarResponse
from app.services.earnings_service import (
    get_earnings_for_symbols,
)

router = APIRouter()


@router.get(
    "/calendar",
    response_model=EarningsCalendarResponse,
    summary="Get upcoming earnings for multiple symbols",
)
async def get_earnings_calendar(
    symbols: str = Query(
        ..., description="Comma-separated symbols, e.g. AAPL,MSFT,NVDA"
    ),
) -> EarningsCalendarResponse:
    """Fetch upcoming earnings for portfolio/watchlist symbols."""
    sym_list = [s.strip().upper() for s in symbols.split(",") if s.strip()][:50]
    events = await get_earnings_for_symbols(sym_list)
    return EarningsCalendarResponse(items=events)
