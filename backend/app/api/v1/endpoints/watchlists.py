from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.limiter import limiter
from app.schemas.watchlist import (
    WatchlistItemAdd,
    WatchlistItemResponse,
    WatchlistListCreate,
    WatchlistListResponse,
    WatchlistListSummary,
    WatchlistListUpdate,
    WatchlistMomentumResponse,
)
from app.services import watchlist_service

router = APIRouter()


@router.get("", response_model=list[WatchlistListSummary])
async def get_watchlists(
    db: AsyncSession = Depends(get_db),
) -> list[WatchlistListSummary]:
    """Return all watchlists with item counts."""
    return await watchlist_service.get_all_lists(db)


@router.post("", response_model=WatchlistListResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def create_watchlist(
    request: Request,
    data: WatchlistListCreate,
    db: AsyncSession = Depends(get_db),
) -> WatchlistListResponse:
    """Create a new watchlist."""
    wl = await watchlist_service.create_list(db, data.name)
    return WatchlistListResponse(
        id=wl.id,
        name=wl.name,
        position=wl.position,
        created_at=wl.created_at,
        items=[],
    )


@router.get("/{list_id}", response_model=WatchlistListResponse)
async def get_watchlist(
    list_id: int,
    db: AsyncSession = Depends(get_db),
) -> WatchlistListResponse:
    """Return a single watchlist with all its items."""
    wl = await watchlist_service.get_list(db, list_id)
    if not wl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Watchlist {list_id} not found",
        )
    return WatchlistListResponse.model_validate(wl)


@router.put("/{list_id}", response_model=WatchlistListResponse)
async def rename_watchlist(
    list_id: int,
    data: WatchlistListUpdate,
    db: AsyncSession = Depends(get_db),
) -> WatchlistListResponse:
    """Rename a watchlist."""
    wl = await watchlist_service.rename_list(db, list_id, data.name)
    if not wl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Watchlist {list_id} not found",
        )
    return WatchlistListResponse.model_validate(wl)


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_watchlist(
    list_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a watchlist and all its items."""
    deleted = await watchlist_service.delete_list(db, list_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Watchlist {list_id} not found",
        )


@router.post(
    "/{list_id}/items",
    response_model=WatchlistItemResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("30/minute")
async def add_item(
    request: Request,
    list_id: int,
    data: WatchlistItemAdd,
    db: AsyncSession = Depends(get_db),
) -> WatchlistItemResponse:
    """Add a stock to a watchlist."""
    wl = await watchlist_service.get_list(db, list_id)
    if not wl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Watchlist {list_id} not found",
        )
    try:
        item = await watchlist_service.add_item(
            db,
            list_id=list_id,
            symbol=data.symbol,
            name=data.name,
            exchange=data.exchange,
            sector=data.sector,
        )
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{data.symbol.upper()} is already in this watchlist",
        ) from None
    return WatchlistItemResponse.model_validate(item)


@router.delete("/{list_id}/items/{symbol}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_item(
    list_id: int,
    symbol: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove a stock from a watchlist."""
    removed = await watchlist_service.remove_item(db, list_id, symbol)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{symbol.upper()} not found in watchlist {list_id}",
        )


@router.get("/{list_id}/signals/momentum", response_model=WatchlistMomentumResponse)
@limiter.limit("20/minute")
async def get_momentum_signals(
    request: Request,
    list_id: int,
    symbols: str = "",
) -> WatchlistMomentumResponse:
    """Return symbols with statistically unusual momentum (|Z-score| >= 2.0).

    Pass symbols as a comma-separated query param, e.g. ?symbols=AAPL,MSFT,NVDA.
    list_id scopes the endpoint for future ACL use; no DB lookup is performed.
    """
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    signals = await watchlist_service.compute_momentum_signals(symbol_list)
    return WatchlistMomentumResponse(signals=signals)
