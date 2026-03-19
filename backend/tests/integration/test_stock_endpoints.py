"""Integration tests for stock API endpoints."""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.models.stock import Stock


@pytest.mark.asyncio
async def test_list_stocks_empty(client: TestClient):
    """Test listing stocks when database is empty."""
    response = client.get("/api/v1/stocks")

    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []
    assert data["meta"]["total"] == 0
    assert data["meta"]["page"] == 1
    assert data["meta"]["limit"] == 20


@pytest.mark.asyncio
async def test_list_stocks_with_data(client: TestClient, db_session):
    """Test listing stocks with data."""
    # Create test stocks
    stocks = [
        Stock(symbol="AAPL", name="Apple Inc.", exchange="NASDAQ", sector="Technology"),
        Stock(symbol="GOOGL", name="Alphabet Inc.", exchange="NASDAQ", sector="Technology"),
        Stock(symbol="MSFT", name="Microsoft Corp.", exchange="NASDAQ", sector="Technology"),
    ]
    for stock in stocks:
        db_session.add(stock)
    await db_session.commit()

    response = client.get("/api/v1/stocks")

    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 3
    assert data["meta"]["total"] == 3


@pytest.mark.asyncio
async def test_list_stocks_pagination(client: TestClient, db_session):
    """Test stock listing with pagination."""
    # Create 5 stocks
    for i in range(5):
        stock = Stock(
            symbol=f"STOCK{i}",
            name=f"Stock {i}",
            exchange="NASDAQ",
            sector="Technology",
        )
        db_session.add(stock)
    await db_session.commit()

    # Test first page
    response = client.get("/api/v1/stocks?page=1&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2
    assert data["meta"]["page"] == 1
    assert data["meta"]["limit"] == 2
    assert data["meta"]["total"] == 5
    assert data["meta"]["total_pages"] == 3

    # Test second page
    response = client.get("/api/v1/stocks?page=2&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2
    assert data["meta"]["page"] == 2


@pytest.mark.asyncio
async def test_get_stock_by_symbol_success(client: TestClient, db_session):
    """Test getting a stock by symbol."""
    stock = Stock(
        symbol="AAPL",
        name="Apple Inc.",
        exchange="NASDAQ",
        sector="Technology",
    )
    db_session.add(stock)
    await db_session.commit()

    response = client.get("/api/v1/stocks/AAPL")

    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "AAPL"
    assert data["name"] == "Apple Inc."


@pytest.mark.asyncio
async def test_get_stock_by_symbol_not_found(client: TestClient):
    """Test getting non-existent stock returns 404."""
    response = client.get("/api/v1/stocks/INVALID")

    assert response.status_code == 404
    body = response.json()
    msg = body.get("error", {}).get("message", body.get("detail", ""))
    assert "not found" in str(msg).lower()


@pytest.mark.asyncio
async def test_create_stock_success(client: TestClient):
    """Test creating a new stock."""
    stock_data = {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "exchange": "NASDAQ",
        "sector": "Technology",
    }

    response = client.post("/api/v1/stocks", json=stock_data)

    assert response.status_code == 201
    data = response.json()
    assert data["symbol"] == "AAPL"
    assert data["name"] == "Apple Inc."
    assert "id" in data


@pytest.mark.asyncio
async def test_create_stock_duplicate_returns_409(client: TestClient, db_session):
    """Test creating duplicate stock returns 409."""
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
    stock_data = {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "exchange": "NASDAQ",
        "sector": "Technology",
    }

    response = client.post("/api/v1/stocks", json=stock_data)

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_stock_validation_error(client: TestClient):
    """Test creating stock with invalid data returns 422."""
    stock_data = {
        "symbol": "",  # Invalid: empty symbol
        "name": "Test",
    }

    response = client.post("/api/v1/stocks", json=stock_data)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_stock_success(client: TestClient, db_session):
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
    update_data = {
        "name": "Apple Corporation",
        "sector": "Tech",
    }

    response = client.put("/api/v1/stocks/AAPL", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Apple Corporation"
    assert data["sector"] == "Tech"


@pytest.mark.asyncio
async def test_update_stock_not_found(client: TestClient):
    """Test updating non-existent stock returns 404."""
    update_data = {"name": "New Name"}

    response = client.put("/api/v1/stocks/INVALID", json=update_data)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_stock_success(client: TestClient, db_session):
    """Test deleting an existing stock."""
    stock = Stock(
        symbol="AAPL",
        name="Apple Inc.",
        exchange="NASDAQ",
        sector="Technology",
    )
    db_session.add(stock)
    await db_session.commit()

    response = client.delete("/api/v1/stocks/AAPL")

    assert response.status_code == 204

    # Verify deleted
    get_response = client.get("/api/v1/stocks/AAPL")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_stock_not_found(client: TestClient):
    """Test deleting non-existent stock returns 404."""
    response = client.delete("/api/v1/stocks/INVALID")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_search_stocks_success(client: TestClient):
    """Test stock search returns results from yfinance."""
    from app.schemas.stock import StockSearchResult

    with patch("app.api.v1.endpoints.stocks.stock_service.search_stocks_from_yfinance") as mock_search:
        mock_search.return_value = [
            StockSearchResult(
                symbol="HIMS",
                name="Hims & Hers Health Inc.",
                exchange="NYSE",
                sector="Healthcare",
                industry="Drug Manufacturers",
                current_price=12.50,
                currency="USD",
                country="United States",
                sparkline=[12.0, 12.2, 12.5],
            ),
        ]

        response = client.get("/api/v1/stocks/search?q=HIMS")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["symbol"] == "HIMS"
        assert "Hims" in data[0]["name"]
        mock_search.assert_called_once_with("HIMS", limit=8)


@pytest.mark.asyncio
async def test_search_stocks_empty(client: TestClient):
    """Test stock search returns empty when no results."""
    with patch("app.api.v1.endpoints.stocks.stock_service.search_stocks_from_yfinance") as mock_search:
        mock_search.return_value = []

        response = client.get("/api/v1/stocks/search?q=INVALID123")

        assert response.status_code == 200
        assert response.json() == []


@pytest.mark.asyncio
async def test_get_stock_data_success(client: TestClient):
    """Test fetching live stock data via FMP."""
    from unittest.mock import AsyncMock as AM
    from app.schemas.stock import StockDataResponse

    mock_response = StockDataResponse(
        symbol="AAPL",
        name="Apple Inc.",
        current_price=155.0,
        previous_close=150.0,
        change=5.0,
        change_percent=3.33,
        volume=1000000,
        market_cap=2500000000000.0,
        currency="USD",
    )

    with patch(
        "app.api.v1.endpoints.stocks.stock_service.fetch_stock_data_from_yfinance",
        new_callable=AM,
        return_value=mock_response,
    ):
        response = client.get("/api/v1/stocks/AAPL/data")

    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "AAPL"
    assert "current_price" in data
    assert "change" in data
