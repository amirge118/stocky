"""Extra unit tests for app/core/telegram.py — covering previously uncovered lines."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.alert import ConditionType


# ── send_alert_message: generic exception path (lines 70-72) ──────────────────


@pytest.mark.asyncio
async def test_send_alert_message_generic_exception_does_not_raise():
    """A non-HTTP exception during POST is caught and swallowed (lines 70-72)."""
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=RuntimeError("network blip"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.core.telegram.settings") as mock_settings,
        patch("app.core.telegram.httpx.AsyncClient", return_value=mock_client),
    ):
        mock_settings.telegram_token = "test-token"
        mock_settings.telegram_chat_id = "chat-999"

        from app.core.telegram import send_alert_message

        # Must not raise even though the underlying POST raises RuntimeError
        await send_alert_message("AAPL", ConditionType.ABOVE, Decimal("150"), 160.0)

    mock_client.post.assert_awaited_once()


# ── send_alert_message: all retries exhausted (line 74) ──────────────────────


@pytest.mark.asyncio
async def test_send_alert_message_exhausts_retries():
    """When every attempt gets a 429 the function logs 'max retries exceeded' (line 74)."""
    rate_limit_response = MagicMock()
    rate_limit_response.status_code = 429
    rate_limit_response.headers = {"Retry-After": "1"}

    mock_client = AsyncMock()
    # Always return 429 → loop exhausts all 3 attempts
    mock_client.post = AsyncMock(return_value=rate_limit_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.core.telegram.settings") as mock_settings,
        patch("app.core.telegram.httpx.AsyncClient", return_value=mock_client),
        patch("app.core.telegram.asyncio.sleep", new_callable=AsyncMock),
    ):
        mock_settings.telegram_token = "test-token"
        mock_settings.telegram_chat_id = "chat-999"

        from app.core.telegram import send_alert_message

        # Should complete without raising
        await send_alert_message("AAPL", ConditionType.ABOVE, Decimal("150"), 160.0)

    # All 3 retry attempts were made
    assert mock_client.post.await_count == 3


# ── send_test_message ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_test_message_no_token_returns_false():
    """Returns (False, token-message) immediately when token is not configured."""
    with patch("app.core.telegram.settings") as mock_settings:
        mock_settings.telegram_token = ""

        from app.core.telegram import send_test_message

        ok, msg = await send_test_message("chat-123")

    assert ok is False
    assert "token" in msg.lower()


@pytest.mark.asyncio
async def test_send_test_message_success():
    """Returns (True, success-message) on HTTP 200."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.headers = {}

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.core.telegram.settings") as mock_settings,
        patch("app.core.telegram.httpx.AsyncClient", return_value=mock_client),
    ):
        mock_settings.telegram_token = "test-token"

        from app.core.telegram import send_test_message

        ok, msg = await send_test_message("chat-123")

    assert ok is True
    assert msg == "Test message sent to Telegram"


@pytest.mark.asyncio
async def test_send_test_message_http_error_returns_false():
    """Returns (False, str(exc)) when raise_for_status raises HTTPStatusError."""
    import httpx

    exc = httpx.HTTPStatusError(
        "403 Forbidden", request=MagicMock(), response=MagicMock()
    )

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=exc)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.core.telegram.settings") as mock_settings,
        patch("app.core.telegram.httpx.AsyncClient", return_value=mock_client),
    ):
        mock_settings.telegram_token = "test-token"

        from app.core.telegram import send_test_message

        ok, msg = await send_test_message("chat-123")

    assert ok is False
    assert "403" in msg


@pytest.mark.asyncio
async def test_send_test_message_generic_exception_returns_false():
    """Returns (False, str(exc)) when a generic exception is raised."""
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=OSError("connection refused"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.core.telegram.settings") as mock_settings,
        patch("app.core.telegram.httpx.AsyncClient", return_value=mock_client),
    ):
        mock_settings.telegram_token = "test-token"

        from app.core.telegram import send_test_message

        ok, msg = await send_test_message("chat-123")

    assert ok is False
    assert "connection refused" in msg


@pytest.mark.asyncio
async def test_send_test_message_max_retries_exhausted():
    """Returns (False, 'Telegram: max retries exceeded') after all attempts get 429."""
    rate_limit_response = MagicMock()
    rate_limit_response.status_code = 429
    rate_limit_response.headers = {"Retry-After": "1"}

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=rate_limit_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.core.telegram.settings") as mock_settings,
        patch("app.core.telegram.httpx.AsyncClient", return_value=mock_client),
        patch("app.core.telegram.asyncio.sleep", new_callable=AsyncMock),
    ):
        mock_settings.telegram_token = "test-token"

        from app.core.telegram import send_test_message

        ok, msg = await send_test_message("chat-123")

    assert ok is False
    assert msg == "Telegram: max retries exceeded"
    assert mock_client.post.await_count == 3
