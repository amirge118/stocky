"""Integration tests for portfolio (holding) API endpoints — extended coverage."""
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.schemas.agent import SectorBreakdownResponse, SectorSlice
from app.schemas.holding import (
    PortfolioHistoryResponse,
    PortfolioPosition,
    PortfolioSummary,
    PortfolioSummaryWithSector,
)
from app.schemas.stock import PortfolioNewsItem


def _make_portfolio_summary() -> PortfolioSummary:
    return PortfolioSummary(
        positions=[
            PortfolioPosition(
                symbol="AAPL",
                name="Apple Inc.",
                shares=10.0,
                avg_cost=150.0,
                total_cost=1500.0,
                current_price=175.0,
                current_value=1750.0,
                gain_loss=250.0,
                gain_loss_pct=16.67,
                portfolio_pct=100.0,
            )
        ],
        total_value=1750.0,
        total_cost=1500.0,
        total_gain_loss=250.0,
        total_gain_loss_pct=16.67,
        total_day_change=50.0,
        total_day_change_pct=2.94,
    )


def _make_sector_breakdown() -> SectorBreakdownResponse:
    return SectorBreakdownResponse(
        sectors=[
            SectorSlice(
                sector="Technology",
                total_value=1750.0,
                weight_pct=100.0,
                symbols=["AAPL"],
                num_holdings=1,
            )
        ],
        total_value=1750.0,
    )


# ── GET /portfolio ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_portfolio_success(client: TestClient):
    mock_result = _make_portfolio_summary()
    with patch(
        "app.api.v1.endpoints.portfolio.holding_service.get_portfolio",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        r = client.get("/api/v1/portfolio")

    assert r.status_code == 200
    data = r.json()
    assert "positions" in data
    assert data["total_value"] == 1750.0


# ── GET /portfolio/summary ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_portfolio_summary_success(client: TestClient):
    portfolio = _make_portfolio_summary()
    sector = _make_sector_breakdown()
    with patch(
        "app.api.v1.endpoints.portfolio.holding_service.get_portfolio_summary",
        new_callable=AsyncMock,
        return_value=(portfolio, sector),
    ):
        r = client.get("/api/v1/portfolio/summary")

    assert r.status_code == 200
    data = r.json()
    assert "portfolio" in data
    assert "sector_breakdown" in data
    assert data["portfolio"]["total_value"] == 1750.0
    assert len(data["sector_breakdown"]["sectors"]) == 1


# ── POST /portfolio ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_add_holding_success(client: TestClient):
    from datetime import date
    from unittest.mock import MagicMock

    mock_holding = MagicMock()
    mock_holding.symbol = "AAPL"
    mock_holding.name = "Apple Inc."
    mock_holding.shares = 10.0
    mock_holding.avg_cost = 150.0
    mock_holding.total_cost = 1500.0

    with patch(
        "app.api.v1.endpoints.portfolio.holding_service.upsert_holding",
        new_callable=AsyncMock,
        return_value=mock_holding,
    ):
        r = client.post(
            "/api/v1/portfolio",
            json={
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "shares": 10.0,
                "price_per_share": 150.0,
                "purchase_date": str(date.today()),
            },
        )

    assert r.status_code == 201
    data = r.json()
    assert data["symbol"] == "AAPL"
    assert data["shares"] == 10.0


# ── GET /portfolio/history ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_portfolio_history_success(client: TestClient):
    mock_result = PortfolioHistoryResponse(period="1m", data=[])
    with patch(
        "app.api.v1.endpoints.portfolio.holding_service.get_portfolio_history",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        r = client.get("/api/v1/portfolio/history?period=1m")

    assert r.status_code == 200
    data = r.json()
    assert data["period"] == "1m"
    assert data["data"] == []


# ── GET /portfolio/news ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_portfolio_news_success(client: TestClient):
    mock_result = [
        PortfolioNewsItem(
            symbol="AAPL",
            title="Apple reports record revenue",
            publisher="Reuters",
            link="https://reuters.com/apple",
            published_at=1_700_000_000_000,
        )
    ]
    with patch(
        "app.api.v1.endpoints.portfolio.holding_service.get_portfolio_news",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        r = client.get("/api/v1/portfolio/news")

    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["symbol"] == "AAPL"
    assert data[0]["title"] == "Apple reports record revenue"


# ── DELETE /portfolio/{symbol} ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_remove_holding_success(client: TestClient):
    with patch(
        "app.api.v1.endpoints.portfolio.holding_service.delete_holding",
        new_callable=AsyncMock,
        return_value=True,
    ):
        r = client.delete("/api/v1/portfolio/AAPL")

    assert r.status_code == 204


@pytest.mark.asyncio
async def test_remove_holding_not_found(client: TestClient):
    with patch(
        "app.api.v1.endpoints.portfolio.holding_service.delete_holding",
        new_callable=AsyncMock,
        return_value=False,
    ):
        r = client.delete("/api/v1/portfolio/INVALID")

    assert r.status_code == 404
    data = r.json()
    msg = data.get("error", {}).get("message", data.get("detail", ""))
    assert "INVALID" in str(msg).upper() or "not found" in str(msg).lower()


# ── GET /portfolio/sector-breakdown ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_sector_breakdown_success(client: TestClient):
    mock_result = _make_sector_breakdown()
    with patch(
        "app.api.v1.endpoints.portfolio.holding_service.get_sector_breakdown",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        r = client.get("/api/v1/portfolio/sector-breakdown")

    assert r.status_code == 200
    data = r.json()
    assert "sectors" in data
    assert data["total_value"] == 1750.0
    assert data["sectors"][0]["sector"] == "Technology"
