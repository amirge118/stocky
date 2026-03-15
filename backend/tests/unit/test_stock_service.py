"""Unit tests for stock service."""
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stock import Stock
from app.schemas.stock import StockCreate, StockDataResponse, StockUpdate
from app.services import stock_service


@pytest.mark.asyncio
async def test_get_stock_by_symbol_found(db_session: AsyncSession):
    """Test getting a stock by symbol when it exists."""
    # Create test stock
    stock = Stock(
        symbol="AAPL",
        name="Apple Inc.",
        exchange="NASDAQ",
        sector="Technology",
    )
    db_session.add(stock)
    await db_session.commit()

    # Test
    result = await stock_service.get_stock_by_symbol(db_session, "AAPL")

    assert result is not None
    assert result.symbol == "AAPL"
    assert result.name == "Apple Inc."


@pytest.mark.asyncio
async def test_get_stock_by_symbol_not_found(db_session: AsyncSession):
    """Test getting a stock by symbol when it doesn't exist."""
    result = await stock_service.get_stock_by_symbol(db_session, "INVALID")

    assert result is None


@pytest.mark.asyncio
async def test_get_stock_by_symbol_case_insensitive(db_session: AsyncSession):
    """Test that symbol lookup is case-insensitive."""
    stock = Stock(
        symbol="AAPL",
        name="Apple Inc.",
        exchange="NASDAQ",
        sector="Technology",
    )
    db_session.add(stock)
    await db_session.commit()

    result = await stock_service.get_stock_by_symbol(db_session, "aapl")

    assert result is not None
    assert result.symbol == "AAPL"


@pytest.mark.asyncio
async def test_get_stocks_empty(db_session: AsyncSession):
    """Test getting stocks when database is empty."""
    stocks, total = await stock_service.get_stocks(db_session)

    assert stocks == []
    assert total == 0


@pytest.mark.asyncio
async def test_get_stocks_with_pagination(db_session: AsyncSession):
    """Test getting stocks with pagination."""
    # Create test stocks
    for i in range(5):
        stock = Stock(
            symbol=f"STOCK{i}",
            name=f"Stock {i}",
            exchange="NASDAQ",
            sector="Technology",
        )
        db_session.add(stock)
    await db_session.commit()

    # Test pagination
    stocks, total = await stock_service.get_stocks(db_session, skip=0, limit=2)

    assert len(stocks) == 2
    assert total == 5


@pytest.mark.asyncio
async def test_get_stocks_with_sector_filter(db_session: AsyncSession):
    """Test getting stocks filtered by sector."""
    stocks_data = [
        ("AAPL", "Apple", "Technology"),
        ("GOOGL", "Alphabet", "Technology"),
        ("JPM", "JPMorgan", "Financial"),
    ]
    for symbol, name, sector in stocks_data:
        stock = Stock(symbol=symbol, name=name, exchange="NASDAQ", sector=sector)
        db_session.add(stock)
    await db_session.commit()

    stocks, total = await stock_service.get_stocks(db_session, sector="Technology")

    assert len(stocks) == 2
    assert total == 2
    assert all(s.sector == "Technology" for s in stocks)


@pytest.mark.asyncio
async def test_get_stocks_sector_filter_case_insensitive(db_session: AsyncSession):
    """Test sector filter is case-insensitive."""
    stock = Stock(symbol="AAPL", name="Apple", exchange="NASDAQ", sector="Technology")
    db_session.add(stock)
    await db_session.commit()

    stocks, total = await stock_service.get_stocks(db_session, sector="technology")
    assert len(stocks) == 1
    assert total == 1


@pytest.mark.asyncio
async def test_get_stocks_ordering(db_session: AsyncSession):
    """Test that stocks are ordered by symbol."""
    stocks_data = [
        ("Z", "Stock Z"),
        ("A", "Stock A"),
        ("M", "Stock M"),
    ]

    for symbol, name in stocks_data:
        stock = Stock(
            symbol=symbol,
            name=name,
            exchange="NASDAQ",
            sector="Technology",
        )
        db_session.add(stock)
    await db_session.commit()

    stocks, _ = await stock_service.get_stocks(db_session)

    assert stocks[0].symbol == "A"
    assert stocks[1].symbol == "M"
    assert stocks[2].symbol == "Z"


@pytest.mark.asyncio
async def test_create_stock_success(db_session: AsyncSession):
    """Test creating a new stock."""
    stock_data = StockCreate(
        symbol="AAPL",
        name="Apple Inc.",
        exchange="NASDAQ",
        sector="Technology",
    )

    result = await stock_service.create_stock(db_session, stock_data)

    assert result.symbol == "AAPL"
    assert result.name == "Apple Inc."
    assert result.id is not None


@pytest.mark.asyncio
async def test_create_stock_uppercase_symbol(db_session: AsyncSession):
    """Test that symbol is converted to uppercase."""
    stock_data = StockCreate(
        symbol="aapl",
        name="Apple Inc.",
        exchange="NASDAQ",
        sector="Technology",
    )

    result = await stock_service.create_stock(db_session, stock_data)

    assert result.symbol == "AAPL"


@pytest.mark.asyncio
async def test_create_stock_duplicate_raises_error(db_session: AsyncSession):
    """Test that creating duplicate stock raises HTTPException."""
    # Create first stock
    stock = Stock(
        symbol="AAPL",
        name="Apple Inc.",
        exchange="NASDAQ",
        sector="Technology",
    )
    db_session.add(stock)
    await db_session.commit()

    # Try to create duplicate
    stock_data = StockCreate(
        symbol="AAPL",
        name="Apple Inc.",
        exchange="NASDAQ",
        sector="Technology",
    )

    with pytest.raises(HTTPException) as exc_info:
        await stock_service.create_stock(db_session, stock_data)

    assert exc_info.value.status_code == status.HTTP_409_CONFLICT


@pytest.mark.asyncio
async def test_update_stock_success(db_session: AsyncSession):
    """Test updating an existing stock."""
    # Create stock
    stock = Stock(
        symbol="AAPL",
        name="Apple Inc.",
        exchange="NASDAQ",
        sector="Technology",
    )
    db_session.add(stock)
    await db_session.commit()

    # Update stock
    update_data = StockUpdate(name="Apple Corporation", sector="Tech")
    result = await stock_service.update_stock(db_session, "AAPL", update_data)

    assert result is not None
    assert result.name == "Apple Corporation"
    assert result.sector == "Tech"
    assert result.symbol == "AAPL"  # Unchanged


@pytest.mark.asyncio
async def test_update_stock_partial(db_session: AsyncSession):
    """Test partial update of stock."""
    stock = Stock(
        symbol="AAPL",
        name="Apple Inc.",
        exchange="NASDAQ",
        sector="Technology",
    )
    db_session.add(stock)
    await db_session.commit()

    update_data = StockUpdate(name="Apple Corporation")
    result = await stock_service.update_stock(db_session, "AAPL", update_data)

    assert result.name == "Apple Corporation"
    assert result.exchange == "NASDAQ"  # Unchanged


@pytest.mark.asyncio
async def test_update_stock_not_found(db_session: AsyncSession):
    """Test updating non-existent stock returns None."""
    update_data = StockUpdate(name="New Name")
    result = await stock_service.update_stock(db_session, "INVALID", update_data)

    assert result is None


@pytest.mark.asyncio
async def test_delete_stock_success(db_session: AsyncSession):
    """Test deleting an existing stock."""
    stock = Stock(
        symbol="AAPL",
        name="Apple Inc.",
        exchange="NASDAQ",
        sector="Technology",
    )
    db_session.add(stock)
    await db_session.commit()

    result = await stock_service.delete_stock(db_session, "AAPL")

    assert result is True

    # Verify deleted
    deleted = await stock_service.get_stock_by_symbol(db_session, "AAPL")
    assert deleted is None


@pytest.mark.asyncio
async def test_delete_stock_not_found(db_session: AsyncSession):
    """Test deleting non-existent stock returns False."""
    result = await stock_service.delete_stock(db_session, "INVALID")

    assert result is False


@pytest.mark.asyncio
@patch("app.services.stock_data.yf")
async def test_fetch_stock_data_from_yfinance_success(mock_yf):
    """Test fetching stock data from yfinance successfully."""
    # Mock yfinance response (uses fast_info, not info)
    mock_ticker = MagicMock()
    mock_ticker.fast_info.last_price = 155.0
    mock_ticker.fast_info.previous_close = 150.0
    mock_ticker.fast_info.three_month_average_volume = 1000000
    mock_ticker.fast_info.market_cap = 2500000000000
    mock_ticker.fast_info.currency = "USD"
    mock_ticker.history.return_value = MagicMock(
        empty=False,
        __getitem__=lambda self, key: MagicMock(
            iloc=MagicMock(__getitem__=lambda self, idx: 155.0 if idx == -1 else 1000000)
        ) if key == "Close" else MagicMock(
            iloc=MagicMock(__getitem__=lambda self, idx: 1000000)
        ),
    )
    mock_yf.Ticker.return_value = mock_ticker

    result = await stock_service.fetch_stock_data_from_yfinance("AAPL")

    assert isinstance(result, StockDataResponse)
    assert result.symbol == "AAPL"
    assert result.name == "AAPL"
    assert result.current_price == 155.0
    assert result.previous_close == 150.0
    assert result.change == 5.0
    assert result.currency == "USD"


@pytest.mark.asyncio
@patch("app.services.stock_data.yf")
async def test_fetch_stock_data_empty_history_raises_error(mock_yf):
    """Test that empty history raises HTTPException."""
    mock_ticker = MagicMock()
    mock_ticker.fast_info.last_price = 0
    mock_ticker.fast_info.previous_close = 0
    mock_ticker.fast_info.currency = "USD"
    mock_ticker.history.return_value = MagicMock(empty=True)
    mock_yf.Ticker.return_value = mock_ticker

    with pytest.raises(HTTPException) as exc_info:
        await stock_service.fetch_stock_data_from_yfinance("INVALID")

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
@patch("app.services.stock_data.cache_get")
@patch("app.services.stock_data.cache_set")
@patch("app.services.stock_data.yf")
async def test_search_stocks_from_yfinance_search(mock_yf, mock_cache_set, mock_cache_get):
    """Test stock search returns results from yfinance Search."""
    mock_cache_get.return_value = None

    mock_search_result = MagicMock()
    mock_search_result.quotes = [
        {
            "symbol": "HIMS",
            "longname": "Hims & Hers Health Inc.",
            "shortname": "Hims & Hers",
            "exchange": "NMS",
            "exchDisp": "NASDAQ",
            "sector": "Healthcare",
            "industry": "Drug Manufacturers",
            "quoteType": "EQUITY",
        },
    ]
    mock_yf.Search.return_value = mock_search_result

    mock_series = MagicMock()
    mock_series.dropna.return_value.tolist.return_value = [12.0, 12.2, 12.5]
    mock_df = MagicMock()
    mock_df.empty = False
    mock_df.columns = ["Close"]
    mock_df.__getitem__ = lambda key: mock_series if key == "Close" else MagicMock()

    mock_ticker = MagicMock()
    mock_ticker.fast_info.last_price = 12.50
    mock_ticker.history.return_value = mock_df
    mock_yf.Ticker.return_value = mock_ticker

    results = await stock_service.search_stocks_from_yfinance("HIMS", limit=8)

    assert len(results) == 1
    assert results[0].symbol == "HIMS"
    assert "Hims" in results[0].name
    mock_yf.Search.assert_called_once_with("HIMS", max_results=20)


@pytest.mark.asyncio
@pytest.mark.skip(reason="Fallback runs in thread pool - mock visibility in executor is flaky")
@patch("app.services.stock_data.cache_get")
@patch("app.services.stock_data.cache_set")
@patch("app.services.stock_data.yf")
async def test_search_stocks_from_yfinance_fallback_direct_lookup(mock_yf, mock_cache_set, mock_cache_get):
    """Test stock search fallback when Search returns empty - direct Ticker lookup."""
    mock_cache_get.return_value = None

    mock_search_result = MagicMock()
    mock_search_result.quotes = []
    mock_yf.Search.return_value = mock_search_result

    mock_ticker = MagicMock()
    mock_ticker.info = {
        "symbol": "HIMS",
        "longName": "Hims & Hers Health Inc.",
        "shortName": "Hims & Hers",
        "exchange": "NMS",
        "sector": "Healthcare",
        "industry": "Drug Manufacturers",
        "quoteType": "EQUITY",
    }
    mock_fast_info = MagicMock()
    mock_fast_info.last_price = 12.50
    mock_fast_info.currency = "USD"
    mock_ticker.fast_info = mock_fast_info

    dropna_return = MagicMock()
    dropna_return.tolist.return_value = [12.0, 12.2, 12.5]
    mock_series = MagicMock()
    mock_series.dropna.return_value = dropna_return
    mock_df = MagicMock()
    mock_df.empty = False
    mock_df.columns = ["Close"]
    mock_df.__getitem__ = lambda key: mock_series if key == "Close" else MagicMock()
    mock_ticker.history.return_value = mock_df

    mock_yf.Ticker.return_value = mock_ticker

    results = await stock_service.search_stocks_from_yfinance("HIMS", limit=8)

    assert len(results) == 1
    assert results[0].symbol == "HIMS"
    assert "Hims" in results[0].name
    assert results[0].current_price == 12.50


@pytest.mark.asyncio
@patch("app.services.stock_data.cache_get")
@patch("app.services.stock_data.yf")
async def test_fetch_stock_data_exception_handling(mock_yf, mock_cache_get):
    """Test that exceptions (yf failure) return 404 when data not found."""
    mock_cache_get.return_value = None
    mock_yf.Ticker.side_effect = Exception("Network error")

    with pytest.raises(HTTPException) as exc_info:
        await stock_service.fetch_stock_data_from_yfinance("NONEXISTENT")

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in str(exc_info.value.detail).lower()
