"""Integration tests for alert API endpoints."""

import pytest
from fastapi.testclient import TestClient

# ── Helpers ───────────────────────────────────────────────────────────────────

def _create_alert(
    client: TestClient,
    ticker: str = "AAPL",
    condition_type: str = "ABOVE",
    target_price: float = 200.0,
) -> dict:
    r = client.post(
        "/api/v1/alerts",
        json={"ticker": ticker, "condition_type": condition_type, "target_price": target_price},
    )
    assert r.status_code == 201
    return r.json()


# ── POST /alerts ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_alert_success(client: TestClient):
    r = client.post(
        "/api/v1/alerts",
        json={"ticker": "AAPL", "condition_type": "ABOVE", "target_price": 200.0},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["ticker"] == "AAPL"
    assert data["condition_type"] == "ABOVE"
    assert float(data["target_price"]) == 200.0
    assert data["is_active"] is True
    assert data["last_triggered"] is None
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_alert_ticker_uppercased(client: TestClient):
    r = client.post(
        "/api/v1/alerts",
        json={"ticker": "aapl", "condition_type": "BELOW", "target_price": 100.0},
    )
    assert r.status_code == 201
    assert r.json()["ticker"] == "AAPL"


@pytest.mark.asyncio
async def test_create_alert_below(client: TestClient):
    r = client.post(
        "/api/v1/alerts",
        json={"ticker": "TSLA", "condition_type": "BELOW", "target_price": 150.0},
    )
    assert r.status_code == 201
    assert r.json()["condition_type"] == "BELOW"


@pytest.mark.asyncio
async def test_create_alert_equal(client: TestClient):
    r = client.post(
        "/api/v1/alerts",
        json={"ticker": "MSFT", "condition_type": "EQUAL", "target_price": 300.0},
    )
    assert r.status_code == 201
    assert r.json()["condition_type"] == "EQUAL"


@pytest.mark.asyncio
async def test_create_alert_missing_ticker(client: TestClient):
    r = client.post(
        "/api/v1/alerts",
        json={"condition_type": "ABOVE", "target_price": 100.0},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_alert_invalid_condition(client: TestClient):
    r = client.post(
        "/api/v1/alerts",
        json={"ticker": "AAPL", "condition_type": "SIDEWAYS", "target_price": 100.0},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_alert_zero_price_rejected(client: TestClient):
    r = client.post(
        "/api/v1/alerts",
        json={"ticker": "AAPL", "condition_type": "ABOVE", "target_price": 0},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_alert_negative_price_rejected(client: TestClient):
    r = client.post(
        "/api/v1/alerts",
        json={"ticker": "AAPL", "condition_type": "ABOVE", "target_price": -10.0},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_alert_ticker_too_long_rejected(client: TestClient):
    r = client.post(
        "/api/v1/alerts",
        json={"ticker": "TOOLONGTICKERX", "condition_type": "ABOVE", "target_price": 100.0},
    )
    assert r.status_code == 422


# ── GET /alerts ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_alerts_empty(client: TestClient):
    r = client.get("/api/v1/alerts")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_list_alerts_returns_created(client: TestClient):
    _create_alert(client, "AAPL")
    _create_alert(client, "MSFT")

    r = client.get("/api/v1/alerts")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_list_alerts_limit(client: TestClient):
    for i in range(5):
        _create_alert(client, f"AA{i:02d}")

    r = client.get("/api/v1/alerts?limit=2")
    assert r.status_code == 200
    assert len(r.json()) == 2


@pytest.mark.asyncio
async def test_list_alerts_offset(client: TestClient):
    _create_alert(client, "AAPL")
    _create_alert(client, "MSFT")
    _create_alert(client, "TSLA")

    r = client.get("/api/v1/alerts?limit=10&offset=2")
    assert r.status_code == 200
    assert len(r.json()) == 1


# ── GET /alerts/{id} ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_alert_by_id(client: TestClient):
    created = _create_alert(client, "NVDA", "BELOW", 500.0)
    r = client.get(f"/api/v1/alerts/{created['id']}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == created["id"]
    assert data["ticker"] == "NVDA"


@pytest.mark.asyncio
async def test_get_alert_not_found(client: TestClient):
    r = client.get("/api/v1/alerts/9999")
    assert r.status_code == 404


# ── PATCH /alerts/{id} ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_patch_alert_deactivate(client: TestClient):
    created = _create_alert(client)
    assert created["is_active"] is True

    r = client.patch(f"/api/v1/alerts/{created['id']}", json={"is_active": False})
    assert r.status_code == 200
    assert r.json()["is_active"] is False


@pytest.mark.asyncio
async def test_patch_alert_reactivate(client: TestClient):
    created = _create_alert(client)
    client.patch(f"/api/v1/alerts/{created['id']}", json={"is_active": False})

    r = client.patch(f"/api/v1/alerts/{created['id']}", json={"is_active": True})
    assert r.status_code == 200
    assert r.json()["is_active"] is True


@pytest.mark.asyncio
async def test_patch_alert_target_price(client: TestClient):
    created = _create_alert(client, target_price=100.0)

    r = client.patch(f"/api/v1/alerts/{created['id']}", json={"target_price": 250.0})
    assert r.status_code == 200
    assert float(r.json()["target_price"]) == 250.0


@pytest.mark.asyncio
async def test_patch_alert_not_found(client: TestClient):
    r = client.patch("/api/v1/alerts/9999", json={"is_active": False})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_patch_alert_invalid_price(client: TestClient):
    created = _create_alert(client)
    r = client.patch(f"/api/v1/alerts/{created['id']}", json={"target_price": -5.0})
    assert r.status_code == 422


# ── DELETE /alerts/{id} ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_alert(client: TestClient):
    created = _create_alert(client)
    r = client.delete(f"/api/v1/alerts/{created['id']}")
    assert r.status_code == 204

    r2 = client.get(f"/api/v1/alerts/{created['id']}")
    assert r2.status_code == 404


@pytest.mark.asyncio
async def test_delete_alert_not_found(client: TestClient):
    r = client.delete("/api/v1/alerts/9999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_delete_alert_does_not_affect_others(client: TestClient):
    a1 = _create_alert(client, "AAPL")
    a2 = _create_alert(client, "MSFT")

    client.delete(f"/api/v1/alerts/{a1['id']}")

    r = client.get("/api/v1/alerts")
    ids = [a["id"] for a in r.json()]
    assert a1["id"] not in ids
    assert a2["id"] in ids
