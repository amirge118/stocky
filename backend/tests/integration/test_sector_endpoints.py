"""Integration tests for sector-browser endpoints: GET /stocks/sectors and GET /stocks/by-sector."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.sector_universe import SECTOR_DISPLAY_ORDER, SECTOR_UNIVERSE


# ── GET /stocks/sectors ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_sectors_returns_list_of_strings(client: TestClient) -> None:
    r = client.get("/api/v1/stocks/sectors")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) > 0
    for item in data:
        assert isinstance(item, str)


@pytest.mark.asyncio
async def test_list_sectors_contains_curated_sectors(client: TestClient) -> None:
    r = client.get("/api/v1/stocks/sectors")
    assert r.status_code == 200
    sectors = r.json()
    for curated in ["Technology", "Healthcare", "Financials", "ETFs"]:
        assert curated in sectors, f"Expected curated sector '{curated}' in response"


@pytest.mark.asyncio
async def test_list_sectors_curated_appear_before_db_only(client: TestClient) -> None:
    """Curated sectors should appear first (stable display order)."""
    r = client.get("/api/v1/stocks/sectors")
    assert r.status_code == 200
    sectors = r.json()
    # First N sectors should match the curated display order
    curated_in_response = [s for s in sectors if s in SECTOR_DISPLAY_ORDER]
    # They should appear in the same relative order as SECTOR_DISPLAY_ORDER
    expected_order = [s for s in SECTOR_DISPLAY_ORDER if s in curated_in_response]
    assert curated_in_response == expected_order


# ── GET /stocks/by-sector ────────────────────────────────────────────────────

MOCK_BATCH_RESULT = {
    "AAPL": type("D", (), {
        "name": "Apple Inc.", "current_price": 191.50, "change_percent": 1.2,
    })(),
    "MSFT": type("D", (), {
        "name": "Microsoft Corp.", "current_price": 380.00, "change_percent": 0.8,
    })(),
}

MOCK_INFO = type("I", (), {
    "sector": "Technology", "industry": "Consumer Electronics",
    "pe_ratio": 28.5, "market_cap": 2900000000000,
})()


@pytest.mark.asyncio
async def test_browse_by_sector_technology_returns_list(client: TestClient) -> None:
    with (
        patch(
            "app.services.stock_service.fetch_stock_data_batch",
            new_callable=AsyncMock,
            return_value=MOCK_BATCH_RESULT,
        ),
        patch(
            "app.services.stock_service.fetch_stock_info",
            new_callable=AsyncMock,
            return_value=MOCK_INFO,
        ),
        patch("app.api.v1.endpoints.stocks.cache_get", return_value=None),
        patch("app.api.v1.endpoints.stocks.cache_set", new_callable=AsyncMock),
    ):
        r = client.get("/api/v1/stocks/by-sector?sector=Technology")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) > 0
    # Each item should have the expected shape
    first = data[0]
    assert "symbol" in first
    assert "name" in first
    assert "sector" in first


@pytest.mark.asyncio
async def test_browse_by_sector_unknown_returns_empty_list(client: TestClient) -> None:
    with (
        patch("app.api.v1.endpoints.stocks.cache_get", return_value=None),
        patch("app.api.v1.endpoints.stocks.cache_set", new_callable=AsyncMock),
    ):
        r = client.get("/api/v1/stocks/by-sector?sector=UnknownSectorXYZ")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_browse_by_sector_missing_sector_param_rejected(client: TestClient) -> None:
    r = client.get("/api/v1/stocks/by-sector")
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_browse_by_sector_limit_respected(client: TestClient) -> None:
    with (
        patch(
            "app.services.stock_service.fetch_stock_data_batch",
            new_callable=AsyncMock,
            return_value={},
        ),
        patch(
            "app.services.stock_service.fetch_stock_info",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch("app.api.v1.endpoints.stocks.cache_get", return_value=None),
        patch("app.api.v1.endpoints.stocks.cache_set", new_callable=AsyncMock),
    ):
        r = client.get("/api/v1/stocks/by-sector?sector=Technology&limit=5")
    assert r.status_code == 200
    assert len(r.json()) <= 5


@pytest.mark.asyncio
async def test_browse_by_sector_limit_too_large_rejected(client: TestClient) -> None:
    r = client.get("/api/v1/stocks/by-sector?sector=Technology&limit=9999")
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_browse_by_sector_case_insensitive(client: TestClient) -> None:
    """Sector name lookup should be case-insensitive via get_symbols_for_sector."""
    with (
        patch(
            "app.services.stock_service.fetch_stock_data_batch",
            new_callable=AsyncMock,
            return_value=MOCK_BATCH_RESULT,
        ),
        patch(
            "app.services.stock_service.fetch_stock_info",
            new_callable=AsyncMock,
            return_value=MOCK_INFO,
        ),
        patch("app.api.v1.endpoints.stocks.cache_get", return_value=None),
        patch("app.api.v1.endpoints.stocks.cache_set", new_callable=AsyncMock),
    ):
        r_lower = client.get("/api/v1/stocks/by-sector?sector=technology")
        r_title = client.get("/api/v1/stocks/by-sector?sector=Technology")

    assert r_lower.status_code == 200
    assert r_title.status_code == 200
    # Both should return the same set of symbols (order may differ due to cache)
    syms_lower = {item["symbol"] for item in r_lower.json()}
    syms_title = {item["symbol"] for item in r_title.json()}
    assert syms_lower == syms_title
