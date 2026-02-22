from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session
from app.schemas.stock import (
    StockAIAnalysisResponse,
    StockCreate,
    StockDataResponse,
    StockHistoryResponse,
    StockInfoResponse,
    StockListResponse,
    StockNewsItem,
    StockResponse,
    StockSearchResult,
    StockUpdate,
)
from app.services import stock_service

router = APIRouter()


@router.options("")
async def options_stocks() -> Response:
    """Handle OPTIONS preflight requests for CORS."""
    return Response(status_code=200)


@router.get("", response_model=StockListResponse, summary="List all stocks")
async def list_stocks(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db_session),
) -> StockListResponse:
    """Get a paginated list of all stocks."""
    skip = (page - 1) * limit
    stocks, total = await stock_service.get_stocks(db, skip=skip, limit=limit)

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


@router.get("/search", response_model=list[StockSearchResult], summary="Search stocks")
async def search_stocks(
    q: str = Query(..., min_length=1, description="Ticker or company name query"),
    limit: int = Query(8, ge=1, le=15, description="Max results to return"),
) -> list[StockSearchResult]:
    """Search for stocks by ticker symbol or company name via yfinance."""
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
    """Fetch detailed company information from yfinance."""
    return await stock_service.fetch_stock_info(symbol)


@router.get("/{symbol}/news", response_model=list[StockNewsItem], summary="Get stock news")
async def get_stock_news(
    symbol: str,
    limit: int = Query(8, ge=1, le=20, description="Max news items to return"),
) -> list[StockNewsItem]:
    """Fetch recent news articles for a stock."""
    return await stock_service.fetch_stock_news(symbol, limit=limit)


@router.get("/{symbol}/analysis", response_model=StockAIAnalysisResponse, summary="Get AI stock analysis")
async def get_stock_analysis(symbol: str) -> StockAIAnalysisResponse:
    """Generate an AI-powered analysis for a stock using Anthropic Claude."""
    return await stock_service.generate_ai_analysis(symbol)


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


@router.post("", response_model=StockResponse, status_code=status.HTTP_201_CREATED, summary="Create a new stock")
async def create_stock(
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
