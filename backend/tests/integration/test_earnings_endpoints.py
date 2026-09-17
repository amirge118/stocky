"""Integration tests for earnings API endpoints."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.schemas.earnings import EarningsEvent


def _event(symbol: str, **overrides) -> EarningsEvent:
    defaults = {
        "symbol": symbol,
        "earnings_date": "2026-05-01",
        "eps_estimate": 1.5,
        "eps_actual": None,
        "surprise_pct": None,
        "revenue_estimate": None,
        "revenue_actual": None,
        "is_upcoming": True,
        "days_until": 10,
    }
    defaults.update(overrides)
    return EarningsEvent(**defaults)


@pytest.mark.asyncio
async def test_get_stock_earnings(client: TestClient):
    with patch(
        "app.api.v1.endpoints.stocks.get_earnings_for_symbol",
        return_value=[_event("AAPL")],
    ):
        response = client.get("/api/v1/stocks/AAPL/earnings")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["symbol"] == "AAPL"


@pytest.mark.asyncio
async def test_get_earnings_calendar(client: TestClient):
    with patch(
        "app.api.v1.endpoints.earnings.get_earnings_for_symbols",
        return_value=[_event("AAPL"), _event("MSFT", days_until=3)],
    ):
        response = client.get("/api/v1/earnings/calendar?symbols=AAPL,MSFT")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_get_earnings_calendar_requires_symbols(client: TestClient):
    response = client.get("/api/v1/earnings/calendar")

    assert response.status_code == 422
