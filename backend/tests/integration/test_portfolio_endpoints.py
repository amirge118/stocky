"""Integration tests for portfolio API endpoints."""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.models.holding import Holding


@pytest.mark.asyncio
@patch("app.services.holding_service.fetch_stock_data_from_yfinance")
async def test_get_portfolio_empty(mock_fetch, client: TestClient):
    """Test GET /portfolio when no holdings."""
    response = client.get("/api/v1/portfolio")

    assert response.status_code == 200
    data = response.json()
    assert data["positions"] == []
    assert data["total_value"] == 0
    assert data["total_cost"] == 0
    mock_fetch.assert_not_called()


@pytest.mark.asyncio
@patch("app.services.holding_service.fetch_stock_info")
@patch("app.services.holding_service.fetch_stock_data_from_yfinance")
async def test_get_portfolio_summary_empty(mock_fetch, mock_info, client: TestClient):
    """Test GET /portfolio/summary when no holdings."""
    response = client.get("/api/v1/portfolio/summary")

    assert response.status_code == 200
    data = response.json()
    assert "portfolio" in data
    assert "sector_breakdown" in data
    assert data["portfolio"]["positions"] == []
    assert data["sector_breakdown"]["sectors"] == []
    mock_fetch.assert_not_called()
    mock_info.assert_not_called()


@pytest.mark.asyncio
@patch("app.services.holding_service.fetch_stock_data_from_yfinance")
async def test_get_portfolio_includes_day_change(mock_fetch, client: TestClient, db_session):
    """Test portfolio response includes day_change fields."""
    from app.schemas.stock import StockDataResponse

    holding = Holding(
        symbol="AAPL",
        name="Apple Inc.",
        shares=10.0,
        avg_cost=150.0,
        total_cost=1500.0,
    )
    db_session.add(holding)
    await db_session.commit()

    mock_fetch.return_value = StockDataResponse(
        symbol="AAPL",
        name="Apple",
        current_price=155.0,
        previous_close=150.0,
        change=5.0,
        change_percent=3.33,
        volume=None,
        market_cap=None,
        currency="USD",
    )

    response = client.get("/api/v1/portfolio")

    assert response.status_code == 200
    data = response.json()
    assert len(data["positions"]) == 1
    assert data["positions"][0]["day_change"] == 50.0
    assert data["positions"][0]["day_change_percent"] == 3.33
    assert "total_day_change" in data
    assert "total_day_change_pct" in data


@pytest.mark.asyncio
@patch("app.services.holding_service.fetch_stock_news")
async def test_get_portfolio_news_empty(mock_fetch, client: TestClient):
    """Test GET /portfolio/news when no holdings."""
    response = client.get("/api/v1/portfolio/news")

    assert response.status_code == 200
    assert response.json() == []
    mock_fetch.assert_not_called()


@pytest.mark.asyncio
@patch("app.services.holding_service.fetch_stock_history")
async def test_get_portfolio_history_empty(mock_fetch, client: TestClient):
    """Test GET /portfolio/history when no holdings."""
    response = client.get("/api/v1/portfolio/history?period=1m")

    assert response.status_code == 200
    data = response.json()
    assert data["period"] == "1m"
    assert data["data"] == []
    mock_fetch.assert_not_called()


@pytest.mark.asyncio
async def test_add_holding_creates_position(client: TestClient, db_session):
    """Test POST /portfolio adds a holding."""
    response = client.post(
        "/api/v1/portfolio",
        json={
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "shares": 10,
            "price_per_share": 150.0,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["symbol"] == "AAPL"
    assert data["shares"] == 10
    assert data["total_cost"] == 1500.0
