"""Integration tests for POST /api/v1/alerts/{alert_id}/trigger endpoint."""

from unittest.mock import AsyncMock, MagicMock, patch

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


def _trigger_alert(client: TestClient, alert_id: int, current_price: float = 210.0) -> object:
    return client.post(
        f"/api/v1/alerts/{alert_id}/trigger",
        json={"current_price": current_price},
    )


# ── POST /alerts/{id}/trigger ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_trigger_alert_not_found(client: TestClient):
    """Triggering a non-existent alert returns 404."""
    r = _trigger_alert(client, alert_id=9999)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_trigger_inactive_alert_returns_200_no_notification(client: TestClient):
    """Triggering an inactive alert returns 200 without sending any notification."""
    created = _create_alert(client)
    # Deactivate the alert
    client.patch(f"/api/v1/alerts/{created['id']}", json={"is_active": False})

    with (
        patch("app.api.v1.endpoints.alerts.send_alert_message") as mock_telegram,
        patch("app.api.v1.endpoints.alerts.send_whatsapp_message") as mock_whatsapp,
    ):
        r = _trigger_alert(client, created["id"])

    assert r.status_code == 200
    data = r.json()
    assert data["id"] == created["id"]
    mock_telegram.assert_not_called()
    mock_whatsapp.assert_not_called()


@pytest.mark.asyncio
async def test_trigger_active_alert_basic(client: TestClient):
    """Triggering an active alert returns 200 with the alert data."""
    created = _create_alert(client, ticker="TSLA", condition_type="ABOVE", target_price=300.0)
    assert created["is_active"] is True

    settings_mock = MagicMock()
    settings_mock.telegram_enabled = False
    settings_mock.telegram_chat_id = None
    settings_mock.whatsapp_enabled = False
    settings_mock.whatsapp_phone = None

    with patch(
        "app.api.v1.endpoints.alerts.get_or_create_settings",
        new=AsyncMock(return_value=settings_mock),
    ):
        r = _trigger_alert(client, created["id"], current_price=310.0)

    assert r.status_code == 200
    data = r.json()
    assert data["id"] == created["id"]
    assert data["ticker"] == "TSLA"


@pytest.mark.asyncio
async def test_trigger_alert_with_telegram_enabled(client: TestClient):
    """Triggering an active alert with telegram_enabled dispatches send_alert_message."""
    created = _create_alert(client, ticker="AAPL", condition_type="ABOVE", target_price=200.0)

    settings_mock = MagicMock()
    settings_mock.telegram_enabled = True
    settings_mock.telegram_chat_id = "123"
    settings_mock.whatsapp_enabled = False
    settings_mock.whatsapp_phone = None

    mock_send_telegram = AsyncMock()

    with (
        patch(
            "app.api.v1.endpoints.alerts.get_or_create_settings",
            new=AsyncMock(return_value=settings_mock),
        ),
        patch(
            "app.api.v1.endpoints.alerts.send_alert_message",
            mock_send_telegram,
        ),
    ):
        r = _trigger_alert(client, created["id"], current_price=210.0)

    assert r.status_code == 200
    data = r.json()
    assert data["id"] == created["id"]


@pytest.mark.asyncio
async def test_trigger_alert_with_whatsapp_enabled(client: TestClient):
    """Triggering an active alert with whatsapp_enabled dispatches send_whatsapp_message."""
    created = _create_alert(client, ticker="MSFT", condition_type="BELOW", target_price=150.0)

    settings_mock = MagicMock()
    settings_mock.telegram_enabled = False
    settings_mock.telegram_chat_id = None
    settings_mock.whatsapp_enabled = True
    settings_mock.whatsapp_phone = "+1"

    mock_send_whatsapp = AsyncMock()

    with (
        patch(
            "app.api.v1.endpoints.alerts.get_or_create_settings",
            new=AsyncMock(return_value=settings_mock),
        ),
        patch(
            "app.api.v1.endpoints.alerts.send_whatsapp_message",
            mock_send_whatsapp,
        ),
    ):
        r = _trigger_alert(client, created["id"], current_price=140.0)

    assert r.status_code == 200
    data = r.json()
    assert data["id"] == created["id"]


@pytest.mark.asyncio
async def test_trigger_alert_no_notifications_when_both_disabled(client: TestClient):
    """No notification functions are called when both telegram and whatsapp are disabled."""
    created = _create_alert(client, ticker="NVDA", condition_type="EQUAL", target_price=500.0)

    settings_mock = MagicMock()
    settings_mock.telegram_enabled = False
    settings_mock.telegram_chat_id = None
    settings_mock.whatsapp_enabled = False
    settings_mock.whatsapp_phone = None

    with (
        patch(
            "app.api.v1.endpoints.alerts.get_or_create_settings",
            new=AsyncMock(return_value=settings_mock),
        ),
        patch(
            "app.api.v1.endpoints.alerts.send_alert_message",
        ) as mock_telegram,
        patch(
            "app.api.v1.endpoints.alerts.send_whatsapp_message",
        ) as mock_whatsapp,
    ):
        r = _trigger_alert(client, created["id"], current_price=500.0)

    assert r.status_code == 200
    mock_telegram.assert_not_called()
    mock_whatsapp.assert_not_called()
