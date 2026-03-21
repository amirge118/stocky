"""Integration tests for notification settings API endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

# ── GET /notifications ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_notification_settings_returns_200(client: TestClient):
    r = client.get("/api/v1/settings/notifications")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_get_notification_settings_has_expected_fields(client: TestClient):
    r = client.get("/api/v1/settings/notifications")
    data = r.json()

    assert "id" in data
    assert "telegram_enabled" in data
    assert "telegram_chat_id" in data
    assert "browser_push_enabled" in data
    assert "whatsapp_enabled" in data
    assert "whatsapp_phone" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_get_notification_settings_default_values(client: TestClient):
    r = client.get("/api/v1/settings/notifications")
    data = r.json()

    assert data["id"] == 1
    assert data["telegram_enabled"] is False
    assert data["whatsapp_enabled"] is False
    assert data["telegram_chat_id"] is None
    assert data["whatsapp_phone"] is None


# ── PATCH /notifications ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_patch_notification_settings_telegram_chat_id(client: TestClient):
    r = client.patch("/api/v1/settings/notifications", json={"telegram_chat_id": "999"})
    assert r.status_code == 200
    assert r.json()["telegram_chat_id"] == "999"


@pytest.mark.asyncio
async def test_patch_notification_settings_telegram_enabled(client: TestClient):
    r = client.patch("/api/v1/settings/notifications", json={"telegram_enabled": True})
    assert r.status_code == 200
    assert r.json()["telegram_enabled"] is True


@pytest.mark.asyncio
async def test_patch_notification_settings_whatsapp_phone(client: TestClient):
    r = client.patch("/api/v1/settings/notifications", json={"whatsapp_phone": "+1234567890"})
    assert r.status_code == 200
    assert r.json()["whatsapp_phone"] == "+1234567890"


@pytest.mark.asyncio
async def test_patch_notification_settings_partial_does_not_reset_other_fields(
    client: TestClient,
):
    """A partial PATCH must not overwrite fields that were not included."""
    client.patch("/api/v1/settings/notifications", json={"telegram_chat_id": "abc123"})
    r = client.patch("/api/v1/settings/notifications", json={"telegram_enabled": True})
    assert r.status_code == 200
    data = r.json()
    assert data["telegram_enabled"] is True
    assert data["telegram_chat_id"] == "abc123"


# ── POST /notifications/test/telegram ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_test_telegram_success(client: TestClient):
    with patch(
        "app.api.v1.endpoints.settings.send_test_message",
        new=AsyncMock(return_value=(True, "OK")),
    ):
        r = client.post(
            "/api/v1/settings/notifications/test/telegram",
            json={"chat_id": "123"},
        )
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["message"] == "OK"


@pytest.mark.asyncio
async def test_test_telegram_failure(client: TestClient):
    with patch(
        "app.api.v1.endpoints.settings.send_test_message",
        new=AsyncMock(return_value=(False, "no token")),
    ):
        r = client.post(
            "/api/v1/settings/notifications/test/telegram",
            json={"chat_id": "123"},
        )
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is False
    assert data["message"] == "no token"


@pytest.mark.asyncio
async def test_test_telegram_missing_chat_id(client: TestClient):
    r = client.post("/api/v1/settings/notifications/test/telegram", json={})
    assert r.status_code == 422


# ── POST /notifications/test/whatsapp ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_test_whatsapp_success(client: TestClient):
    with patch(
        "app.api.v1.endpoints.settings.send_test_whatsapp_message",
        new=AsyncMock(return_value=(True, "OK")),
    ):
        r = client.post(
            "/api/v1/settings/notifications/test/whatsapp",
            json={"phone": "+1234567890"},
        )
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["message"] == "OK"


@pytest.mark.asyncio
async def test_test_whatsapp_failure(client: TestClient):
    with patch(
        "app.api.v1.endpoints.settings.send_test_whatsapp_message",
        new=AsyncMock(return_value=(False, "invalid phone")),
    ):
        r = client.post(
            "/api/v1/settings/notifications/test/whatsapp",
            json={"phone": "+1234567890"},
        )
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is False
    assert data["message"] == "invalid phone"


@pytest.mark.asyncio
async def test_test_whatsapp_missing_phone(client: TestClient):
    r = client.post("/api/v1/settings/notifications/test/whatsapp", json={})
    assert r.status_code == 422
