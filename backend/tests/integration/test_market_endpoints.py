"""Integration tests for /api/v1/market endpoints."""
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.schemas.market import IndexData, MarketOverviewResponse, MoverData, SectorData


def _overview() -> MarketOverviewResponse:
    return MarketOverviewResponse(
        indices=[
            IndexData(symbol="^GSPC", name="S&P 500", price=4000.0,
                      change=10.0, change_percent=0.25, sparkline=[3990.0, 4000.0]),
            IndexData(symbol="^IXIC", name="NASDAQ", price=14000.0,
                      change=-50.0, change_percent=-0.35, sparkline=[14050.0, 14000.0]),
        ],
        sectors=[
            SectorData(name="Technology", etf="XLK", price=150.0, change_percent=0.5, news=[]),
        ],
        gainers=[
            MoverData(symbol="AAPL", name="AAPL", price=175.0, change_percent=2.5),
            MoverData(symbol="NVDA", name="NVDA", price=800.0, change_percent=1.8),
        ],
        losers=[
            MoverData(symbol="TSLA", name="TSLA", price=200.0, change_percent=-1.5),
        ],
        updated_at="2026-01-01T12:00:00+00:00",
    )


@pytest.mark.asyncio
async def test_market_overview_success(client: TestClient):
    with patch(
        "app.api.v1.endpoints.market.market_service.get_market_overview",
        new_callable=AsyncMock,
        return_value=_overview(),
    ):
        response = client.get("/api/v1/market/overview")

    assert response.status_code == 200
    data = response.json()
    assert "indices" in data
    assert "sectors" in data
    assert "gainers" in data
    assert "losers" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_market_overview_indices_shape(client: TestClient):
    with patch(
        "app.api.v1.endpoints.market.market_service.get_market_overview",
        new_callable=AsyncMock,
        return_value=_overview(),
    ):
        response = client.get("/api/v1/market/overview")

    data = response.json()
    assert len(data["indices"]) == 2
    idx = data["indices"][0]
    assert idx["symbol"] == "^GSPC"
    assert idx["name"] == "S&P 500"
    assert "price" in idx
    assert "change" in idx
    assert "change_percent" in idx
    assert "sparkline" in idx


@pytest.mark.asyncio
async def test_market_overview_movers_shape(client: TestClient):
    with patch(
        "app.api.v1.endpoints.market.market_service.get_market_overview",
        new_callable=AsyncMock,
        return_value=_overview(),
    ):
        response = client.get("/api/v1/market/overview")

    data = response.json()
    assert data["gainers"][0]["symbol"] == "AAPL"
    assert data["losers"][0]["symbol"] == "TSLA"
    assert data["losers"][0]["change_percent"] < 0


@pytest.mark.asyncio
async def test_market_overview_service_error_returns_500(client: TestClient):
    with patch(
        "app.api.v1.endpoints.market.market_service.get_market_overview",
        new_callable=AsyncMock,
        side_effect=RuntimeError("yfinance offline"),
    ):
        response = client.get("/api/v1/market/overview")

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_market_overview_no_auth_required(client: TestClient):
    """Endpoint is public — no token needed."""
    with patch(
        "app.api.v1.endpoints.market.market_service.get_market_overview",
        new_callable=AsyncMock,
        return_value=_overview(),
    ):
        response = client.get("/api/v1/market/overview")

    assert response.status_code != 401
    assert response.status_code != 403
