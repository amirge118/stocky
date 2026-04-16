"""Integration tests for POST /watchlists/{list_id}/items/bulk."""

import pytest
from fastapi.testclient import TestClient


def _create_list(client: TestClient, name: str = "Bulk Test") -> dict:
    r = client.post("/api/v1/watchlists", json={"name": name})
    assert r.status_code == 201
    return r.json()


def _make_item(symbol: str, sector: str = "Technology") -> dict:
    return {
        "symbol": symbol,
        "name": f"{symbol} Inc.",
        "exchange": "NASDAQ",
        "sector": sector,
    }


# ── Bulk add success ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_bulk_add_success_returns_added_list(client: TestClient) -> None:
    wl = _create_list(client)
    r = client.post(
        f"/api/v1/watchlists/{wl['id']}/items/bulk",
        json={"items": [_make_item("AAPL"), _make_item("MSFT"), _make_item("NVDA")]},
    )
    assert r.status_code == 201
    data = r.json()
    assert len(data["added"]) == 3
    assert data["skipped"] == []
    assert data["failed"] == []
    added_syms = {item["symbol"] for item in data["added"]}
    assert added_syms == {"AAPL", "MSFT", "NVDA"}


@pytest.mark.asyncio
async def test_bulk_add_skips_duplicates(client: TestClient) -> None:
    wl = _create_list(client)
    # Pre-add AAPL via the single-item endpoint
    r_single = client.post(
        f"/api/v1/watchlists/{wl['id']}/items",
        json=_make_item("AAPL"),
    )
    assert r_single.status_code == 201

    # Bulk-add [AAPL (dup), MSFT (new)]
    r = client.post(
        f"/api/v1/watchlists/{wl['id']}/items/bulk",
        json={"items": [_make_item("AAPL"), _make_item("MSFT")]},
    )
    assert r.status_code == 201
    data = r.json()
    assert len(data["added"]) == 1
    assert data["added"][0]["symbol"] == "MSFT"
    assert "AAPL" in data["skipped"]
    assert data["failed"] == []


@pytest.mark.asyncio
async def test_bulk_add_single_item_succeeds(client: TestClient) -> None:
    wl = _create_list(client)
    r = client.post(
        f"/api/v1/watchlists/{wl['id']}/items/bulk",
        json={"items": [_make_item("TSLA")]},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["added"][0]["symbol"] == "TSLA"


# ── Error cases ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_bulk_add_watchlist_not_found_returns_404(client: TestClient) -> None:
    r = client.post(
        "/api/v1/watchlists/99999/items/bulk",
        json={"items": [_make_item("AAPL")]},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_bulk_add_empty_items_rejected(client: TestClient) -> None:
    wl = _create_list(client)
    r = client.post(
        f"/api/v1/watchlists/{wl['id']}/items/bulk",
        json={"items": []},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_bulk_add_over_50_items_rejected(client: TestClient) -> None:
    wl = _create_list(client)
    items = [_make_item(f"SYM{i:02d}") for i in range(51)]
    r = client.post(
        f"/api/v1/watchlists/{wl['id']}/items/bulk",
        json={"items": items},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_bulk_add_all_duplicates_returns_empty_added(client: TestClient) -> None:
    wl = _create_list(client)
    for sym in ["AAPL", "MSFT"]:
        client.post(
            f"/api/v1/watchlists/{wl['id']}/items",
            json=_make_item(sym),
        )

    r = client.post(
        f"/api/v1/watchlists/{wl['id']}/items/bulk",
        json={"items": [_make_item("AAPL"), _make_item("MSFT")]},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["added"] == []
    assert set(data["skipped"]) == {"AAPL", "MSFT"}


@pytest.mark.asyncio
async def test_bulk_add_symbols_uppercased(client: TestClient) -> None:
    wl = _create_list(client)
    r = client.post(
        f"/api/v1/watchlists/{wl['id']}/items/bulk",
        json={"items": [{"symbol": "aapl", "name": "Apple Inc.", "exchange": "NASDAQ"}]},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["added"][0]["symbol"] == "AAPL"
