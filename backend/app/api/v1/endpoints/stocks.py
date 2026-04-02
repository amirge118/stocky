from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_get, cache_set
from app.core.dependencies import get_db_session
from app.core.limiter import limiter
from app.schemas.stock import (
    CompareSummaryResponse,
    SectorPeerResponse,
    StockAIAnalysisResponse,
    StockCreate,
    StockDataResponse,
    StockDividendsResponse,
    StockEnrichedData,
    StockHistoryResponse,
    StockIndicatorsResponse,
    StockInfoResponse,
    StockListResponse,
    StockNewsItem,
    StockResponse,
    StockSearchResult,
    StockUpdate,
)
from app.services import stock_service
from app.services.indicators_service import compute_indicators

router = APIRouter()


@router.options("")
async def options_stocks() -> Response:
    """Handle OPTIONS preflight requests for CORS."""
    return Response(status_code=200)


class BatchStockDataRequest(BaseModel):
    """Request body for batch stock data fetch."""

    symbols: list[str] = Field(..., min_length=1, max_length=50)


@router.post("/batch-data", summary="Fetch live data for multiple stocks")
async def get_batch_stock_data(body: BatchStockDataRequest) -> dict[str, StockDataResponse]:
    """Fetch live stock data for up to 50 symbols in one request."""
    result = await stock_service.fetch_stock_data_batch(body.symbols)
    return result


@router.options("/batch-data")
async def options_batch_data() -> Response:
    """Handle OPTIONS preflight for batch-data."""
    return Response(status_code=200)


@router.post("/enriched-batch", summary="Fetch enriched data for multiple stocks")
async def get_enriched_batch(body: BatchStockDataRequest) -> dict[str, StockEnrichedData]:
    """Fetch 52W range, avg volume, and analyst rating for up to 50 symbols. Cached 1hr."""
    return await stock_service.fetch_stock_enriched_batch(body.symbols)


@router.options("/enriched-batch")
async def options_enriched_batch() -> Response:
    """Handle OPTIONS preflight for enriched-batch."""
    return Response(status_code=200)


@router.get("", response_model=StockListResponse, summary="List all stocks")
async def list_stocks(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=500, description="Items per page"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    db: AsyncSession = Depends(get_db_session),
) -> StockListResponse:
    """Get a paginated list of all stocks."""
    skip = (page - 1) * limit
    stocks, total = await stock_service.get_stocks(db, skip=skip, limit=limit, sector=sector)

    total_pages = (total + limit - 1) // limit if total > 0 else 0

    return StockListResponse(
        data=[StockResponse.model_validate(stock) for stock in stocks],
        meta={
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages,
        },
    )


@router.get("/compare-summary", response_model=CompareSummaryResponse, summary="AI compare summary")
async def get_compare_summary(
    symbols: str = Query(..., description="Comma-separated symbols, max 5"),
) -> CompareSummaryResponse:
    """Generate AI comparison summary for given stocks."""
    sym_list = [s.strip().upper() for s in symbols.split(",") if s.strip()][:5]
    return await stock_service.generate_compare_summary(sym_list)


@router.get("/sector-peers", response_model=list[SectorPeerResponse], summary="Get sector peers")
async def get_sector_peers(
    sector: str = Query(..., description="Sector name"),
    symbol: Optional[str] = Query(None, description="Current stock symbol (highlighted in results)"),
    limit: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db_session),
) -> list[SectorPeerResponse]:
    """Get stocks in the same sector with price and fundamentals."""
    return await stock_service.get_sector_peers(db, sector=sector, current_symbol=symbol, limit=limit)


@router.get("/search", response_model=list[StockSearchResult], summary="Search stocks")
async def search_stocks(
    q: str = Query(..., min_length=1, description="Ticker or company name query"),
    limit: int = Query(8, ge=1, le=15, description="Max results to return"),
) -> list[StockSearchResult]:
    """Search for stocks by ticker symbol or company name via yfinance."""
    if not q.isascii():
        return []
    return await stock_service.search_stocks_from_yfinance(q, limit=limit)


@router.get("/{symbol}/history", response_model=StockHistoryResponse, summary="Get stock price history")
async def get_stock_history(
    symbol: str,
    period: str = Query("1m", description="Period: 1d | 1w | 1m | 6m | 1y"),
) -> StockHistoryResponse:
    """Fetch OHLCV price history for a stock."""
    return await stock_service.fetch_stock_history(symbol, period=period)


@router.get("/{symbol}/info", response_model=StockInfoResponse, summary="Get detailed company info")
async def get_stock_info(symbol: str) -> StockInfoResponse:
    """Fetch detailed company information from yfinance. Cached 5 minutes."""
    cache_key = f"stock:info:{symbol.upper()}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return StockInfoResponse(**cached)
    result = await stock_service.fetch_stock_info(symbol)
    await cache_set(cache_key, result.model_dump(), ttl=300)
    return result


@router.get("/{symbol}/news", response_model=list[StockNewsItem], summary="Get stock news")
async def get_stock_news(
    symbol: str,
    limit: int = Query(8, ge=1, le=20, description="Max news items to return"),
) -> list[StockNewsItem]:
    """Fetch recent news articles for a stock. Cached 2 minutes."""
    cache_key = f"stock:news:{symbol.upper()}:{limit}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return [StockNewsItem(**item) for item in cached]
    result = await stock_service.fetch_stock_news(symbol, limit=limit)
    await cache_set(cache_key, [item.model_dump() for item in result], ttl=120)
    return result


@router.get("/{symbol}/analysis", response_model=StockAIAnalysisResponse, summary="Get AI stock analysis")
async def get_stock_analysis(symbol: str) -> StockAIAnalysisResponse:
    """Generate an AI-powered analysis for a stock using Anthropic Claude."""
    return await stock_service.generate_ai_analysis(symbol)


@router.get("/{symbol}/dividends", summary="Get dividend history")
async def get_stock_dividends(
    symbol: str,
    years: int = Query(5, ge=1, le=10, description="Number of years of history"),
) -> StockDividendsResponse:
    """Fetch dividend payment history and trailing yield."""
    return await stock_service.fetch_stock_dividends(symbol, years=years)


@router.get("/{symbol}", response_model=StockResponse, summary="Get stock by symbol")
async def get_stock(
    symbol: str,
    db: AsyncSession = Depends(get_db_session),
) -> StockResponse:
    """Get a stock by its symbol."""
    stock = await stock_service.get_stock_by_symbol(db, symbol)
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock with symbol {symbol} not found",
        )
    return StockResponse.model_validate(stock)


@router.get("/{symbol}/indicators", response_model=StockIndicatorsResponse, summary="Get technical indicators")
async def get_stock_indicators(
    symbol: str,
    period: str = Query("6m", description="Period: 1m | 6m | 1y | 2y | 5y"),
) -> StockIndicatorsResponse:
    """Compute RSI, MACD, SMA20, SMA50, and Bollinger Bands from historical price data."""
    sym = symbol.upper()
    cache_key = f"indicators:{sym}:{period}"
    cached = await cache_get(cache_key)
    if cached:
        return StockIndicatorsResponse.model_validate(cached)
    history = await stock_service.fetch_stock_history(sym, period=period)
    result = compute_indicators(sym, period, history.data)
    await cache_set(cache_key, result.model_dump(mode="json"), ttl=300)
    return result


@router.post("", response_model=StockResponse, status_code=status.HTTP_201_CREATED, summary="Create a new stock")
@limiter.limit("30/minute")
async def create_stock(
    request: Request,
    stock_data: StockCreate,
    db: AsyncSession = Depends(get_db_session),
) -> StockResponse:
    """Create a new stock entry."""
    stock = await stock_service.create_stock(db, stock_data)
    return StockResponse.model_validate(stock)


@router.put("/{symbol}", response_model=StockResponse, summary="Update a stock")
async def update_stock(
    symbol: str,
    stock_data: StockUpdate,
    db: AsyncSession = Depends(get_db_session),
) -> StockResponse:
    """Update an existing stock."""
    stock = await stock_service.update_stock(db, symbol, stock_data)
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock with symbol {symbol} not found",
        )
    return StockResponse.model_validate(stock)


@router.delete("/{symbol}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a stock")
async def delete_stock(
    symbol: str,
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete a stock."""
    deleted = await stock_service.delete_stock(db, symbol)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock with symbol {symbol} not found",
        )


@router.get("/{symbol}/data", response_model=StockDataResponse, summary="Fetch live stock data")
async def get_stock_data(symbol: str) -> StockDataResponse:
    """Fetch live stock data from yfinance API."""
    return await stock_service.fetch_stock_data_from_yfinance(symbol)
