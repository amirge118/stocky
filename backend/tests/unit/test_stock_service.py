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
@patch("app.services.stock_service.yf")
async def test_fetch_stock_data_from_yfinance_success(mock_yf):
    """Test fetching stock data from yfinance successfully."""
    # Mock yfinance response
    mock_ticker = MagicMock()
    mock_ticker.info = {
        "longName": "Apple Inc.",
        "previousClose": 150.0,
        "marketCap": 2500000000000,
        "currency": "USD",
    }
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
    assert result.name == "Apple Inc."
    assert result.current_price == 155.0
    assert result.previous_close == 150.0
    assert result.change == 5.0
    assert result.currency == "USD"


@pytest.mark.asyncio
@patch("app.services.stock_service.yf")
async def test_fetch_stock_data_empty_history_raises_error(mock_yf):
    """Test that empty history raises HTTPException."""
    mock_ticker = MagicMock()
    mock_ticker.info = {}
    mock_ticker.history.return_value = MagicMock(empty=True)
    mock_yf.Ticker.return_value = mock_ticker

    with pytest.raises(HTTPException) as exc_info:
        await stock_service.fetch_stock_data_from_yfinance("INVALID")

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
@patch("app.services.stock_service.yf")
async def test_fetch_stock_data_exception_handling(mock_yf):
    """Test that exceptions are properly handled."""
    mock_yf.Ticker.side_effect = Exception("Network error")

    with pytest.raises(HTTPException) as exc_info:
        await stock_service.fetch_stock_data_from_yfinance("AAPL")

    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Error fetching stock data" in str(exc_info.value.detail)
