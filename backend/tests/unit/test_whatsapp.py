"""Unit tests for app/core/whatsapp.py."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.models.alert import ConditionType

# ── send_whatsapp_message ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_whatsapp_no_op_when_token_missing():
    """No HTTP call when whatsapp_token is empty."""
    with (
        patch("app.core.whatsapp.settings") as mock_settings,
        patch("app.core.whatsapp.httpx.AsyncClient") as mock_client_cls,
    ):
        mock_settings.whatsapp_token = ""
        mock_settings.whatsapp_phone_number_id = "12345678"

        from app.core.whatsapp import send_whatsapp_message

        await send_whatsapp_message(
            "AAPL", ConditionType.ABOVE, Decimal("150"), 160.0, "+15551234567"
        )

    mock_client_cls.assert_not_called()


@pytest.mark.asyncio
async def test_send_whatsapp_no_op_when_phone_number_id_missing():
    """No HTTP call when whatsapp_phone_number_id is empty."""
    with (
        patch("app.core.whatsapp.settings") as mock_settings,
        patch("app.core.whatsapp.httpx.AsyncClient") as mock_client_cls,
    ):
        mock_settings.whatsapp_token = "some-token"
        mock_settings.whatsapp_phone_number_id = ""

        from app.core.whatsapp import send_whatsapp_message

        await send_whatsapp_message(
            "AAPL", ConditionType.ABOVE, Decimal("150"), 160.0, "+15551234567"
        )

    mock_client_cls.assert_not_called()


@pytest.mark.asyncio
async def test_send_whatsapp_posts_correct_payload():
    """Makes a POST with the correct payload when fully configured."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.core.whatsapp.settings") as mock_settings,
        patch("app.core.whatsapp.httpx.AsyncClient", return_value=mock_client),
    ):
        mock_settings.whatsapp_token = "test-token"
        mock_settings.whatsapp_phone_number_id = "987654321"

        from app.core.whatsapp import send_whatsapp_message

        await send_whatsapp_message(
            "TSLA", ConditionType.BELOW, Decimal("200"), 190.0, "+15559876543"
        )

    mock_client.post.assert_awaited_once()
    call_kwargs = mock_client.post.call_args
    payload = call_kwargs[1]["json"]
    assert payload["messaging_product"] == "whatsapp"
    assert payload["to"] == "15559876543"  # leading "+" stripped
    assert payload["type"] == "text"
    assert "TSLA" in payload["text"]["body"]
    assert "fell below" in payload["text"]["body"]


@pytest.mark.asyncio
async def test_send_whatsapp_does_not_raise_on_http_status_error():
    """HTTPStatusError is caught and logged — no exception propagates."""
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(
        side_effect=httpx.HTTPStatusError(
            "403", request=MagicMock(), response=MagicMock()
        )
    )
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.core.whatsapp.settings") as mock_settings,
        patch("app.core.whatsapp.httpx.AsyncClient", return_value=mock_client),
    ):
        mock_settings.whatsapp_token = "tok"
        mock_settings.whatsapp_phone_number_id = "pid"

        from app.core.whatsapp import send_whatsapp_message

        # Must not raise
        await send_whatsapp_message(
            "AAPL", ConditionType.ABOVE, Decimal("100"), 110.0, "+15551112222"
        )


@pytest.mark.asyncio
async def test_send_whatsapp_does_not_raise_on_generic_exception():
    """Generic exceptions are caught and logged — no exception propagates."""
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=Exception("network error"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.core.whatsapp.settings") as mock_settings,
        patch("app.core.whatsapp.httpx.AsyncClient", return_value=mock_client),
    ):
        mock_settings.whatsapp_token = "tok"
        mock_settings.whatsapp_phone_number_id = "pid"

        from app.core.whatsapp import send_whatsapp_message

        await send_whatsapp_message(
            "GOOG", ConditionType.EQUAL, Decimal("50"), 50.0, "+15553334444"
        )


# ── send_test_whatsapp_message ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_test_whatsapp_returns_false_when_token_missing():
    with patch("app.core.whatsapp.settings") as mock_settings:
        mock_settings.whatsapp_token = ""
        mock_settings.whatsapp_phone_number_id = "pid"

        from app.core.whatsapp import send_test_whatsapp_message

        ok, msg = await send_test_whatsapp_message("+15550001111")

    assert ok is False
    assert "token" in msg.lower()


@pytest.mark.asyncio
async def test_send_test_whatsapp_returns_false_when_phone_number_id_missing():
    with patch("app.core.whatsapp.settings") as mock_settings:
        mock_settings.whatsapp_token = "tok"
        mock_settings.whatsapp_phone_number_id = ""

        from app.core.whatsapp import send_test_whatsapp_message

        ok, msg = await send_test_whatsapp_message("+15550001111")

    assert ok is False
    assert "phone number id" in msg.lower()


@pytest.mark.asyncio
async def test_send_test_whatsapp_returns_true_on_success():
    """Returns (True, …) when the HTTP call succeeds."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.core.whatsapp.settings") as mock_settings,
        patch("app.core.whatsapp.httpx.AsyncClient", return_value=mock_client),
    ):
        mock_settings.whatsapp_token = "tok"
        mock_settings.whatsapp_phone_number_id = "pid"

        from app.core.whatsapp import send_test_whatsapp_message

        ok, msg = await send_test_whatsapp_message("+15550001111")

    assert ok is True
    assert isinstance(msg, str)
    assert len(msg) > 0


@pytest.mark.asyncio
async def test_send_test_whatsapp_returns_false_on_http_error():
    """Returns (False, error string) on HTTPStatusError."""
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(
        side_effect=httpx.HTTPStatusError(
            "500 Server Error", request=MagicMock(), response=MagicMock()
        )
    )
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.core.whatsapp.settings") as mock_settings,
        patch("app.core.whatsapp.httpx.AsyncClient", return_value=mock_client),
    ):
        mock_settings.whatsapp_token = "tok"
        mock_settings.whatsapp_phone_number_id = "pid"

        from app.core.whatsapp import send_test_whatsapp_message

        ok, msg = await send_test_whatsapp_message("+15550001111")

    assert ok is False
    assert isinstance(msg, str)
