"""Integration tests for watchlist API endpoints."""

import pytest
from fastapi.testclient import TestClient

# ── Helpers ─────────────────────────────────────────────────────────────────

def _create_list(client: TestClient, name: str = "Test List") -> dict:
    r = client.post("/api/v1/watchlists", json={"name": name})
    assert r.status_code == 201
    return r.json()


def _add_item(client: TestClient, list_id: int, symbol: str = "AAPL") -> dict:
    r = client.post(
        f"/api/v1/watchlists/{list_id}/items",
        json={"symbol": symbol, "name": f"{symbol} Inc.", "exchange": "NASDAQ", "sector": "Technology"},
    )
    assert r.status_code == 201
    return r.json()


# ── GET /watchlists ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_watchlists_empty(client: TestClient):
    r = client.get("/api/v1/watchlists")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_list_watchlists_returns_item_count(client: TestClient):
    wl = _create_list(client, "My List")
    _add_item(client, wl["id"], "AAPL")
    _add_item(client, wl["id"], "MSFT")

    r = client.get("/api/v1/watchlists")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["item_count"] == 2
    assert data[0]["name"] == "My List"


# ── POST /watchlists ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_watchlist(client: TestClient):
    r = client.post("/api/v1/watchlists", json={"name": "Tech"})
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Tech"
    assert data["items"] == []
    assert "id" in data


@pytest.mark.asyncio
async def test_create_watchlist_empty_name_rejected(client: TestClient):
    r = client.post("/api/v1/watchlists", json={"name": ""})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_watchlist_name_too_long_rejected(client: TestClient):
    r = client.post("/api/v1/watchlists", json={"name": "x" * 101})
    assert r.status_code == 422


# ── GET /watchlists/{id} ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_watchlist(client: TestClient):
    wl = _create_list(client, "Dividends")
    _add_item(client, wl["id"], "JNJ")

    r = client.get(f"/api/v1/watchlists/{wl['id']}")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Dividends"
    assert len(data["items"]) == 1
    assert data["items"][0]["symbol"] == "JNJ"


@pytest.mark.asyncio
async def test_get_watchlist_not_found(client: TestClient):
    r = client.get("/api/v1/watchlists/9999")
    assert r.status_code == 404


# ── PUT /watchlists/{id} ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_rename_watchlist(client: TestClient):
    wl = _create_list(client, "Old")
    r = client.put(f"/api/v1/watchlists/{wl['id']}", json={"name": "New"})
    assert r.status_code == 200
    assert r.json()["name"] == "New"


@pytest.mark.asyncio
async def test_rename_watchlist_not_found(client: TestClient):
    r = client.put("/api/v1/watchlists/9999", json={"name": "Whatever"})
    assert r.status_code == 404


# ── DELETE /watchlists/{id} ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_watchlist(client: TestClient):
    wl = _create_list(client)
    r = client.delete(f"/api/v1/watchlists/{wl['id']}")
    assert r.status_code == 204

    r2 = client.get(f"/api/v1/watchlists/{wl['id']}")
    assert r2.status_code == 404


@pytest.mark.asyncio
async def test_delete_watchlist_not_found(client: TestClient):
    r = client.delete("/api/v1/watchlists/9999")
    assert r.status_code == 404


# ── POST /watchlists/{id}/items ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_add_item_to_watchlist(client: TestClient):
    wl = _create_list(client)
    r = client.post(
        f"/api/v1/watchlists/{wl['id']}/items",
        json={"symbol": "nvda", "name": "Nvidia", "exchange": "NASDAQ", "sector": "Technology"},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["symbol"] == "NVDA"  # uppercased
    assert data["watchlist_id"] == wl["id"]


@pytest.mark.asyncio
async def test_add_duplicate_item_returns_409(client: TestClient):
    wl = _create_list(client)
    _add_item(client, wl["id"], "AAPL")
    r = client.post(
        f"/api/v1/watchlists/{wl['id']}/items",
        json={"symbol": "AAPL", "name": "Apple", "exchange": "NASDAQ"},
    )
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_add_item_to_nonexistent_list(client: TestClient):
    r = client.post(
        "/api/v1/watchlists/9999/items",
        json={"symbol": "AAPL", "name": "Apple", "exchange": "NASDAQ"},
    )
    assert r.status_code == 404


# ── DELETE /watchlists/{id}/items/{symbol} ───────────────────────────────────

@pytest.mark.asyncio
async def test_remove_item_from_watchlist(client: TestClient):
    wl = _create_list(client)
    _add_item(client, wl["id"], "TSLA")

    r = client.delete(f"/api/v1/watchlists/{wl['id']}/items/TSLA")
    assert r.status_code == 204

    r2 = client.get(f"/api/v1/watchlists/{wl['id']}")
    assert r2.json()["items"] == []


@pytest.mark.asyncio
async def test_remove_item_not_found(client: TestClient):
    wl = _create_list(client)
    r = client.delete(f"/api/v1/watchlists/{wl['id']}/items/ZZZZZ")
    assert r.status_code == 404
