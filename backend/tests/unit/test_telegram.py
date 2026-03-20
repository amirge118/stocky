"""Unit tests for Telegram notification helper."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.alert import ConditionType

# ── send_alert_message ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_send_alert_no_op_when_token_missing():
    """No HTTP call when telegram_token is empty."""
    with (
        patch("app.core.telegram.settings") as mock_settings,
        patch("app.core.telegram.httpx.AsyncClient") as mock_client_cls,
    ):
        mock_settings.telegram_token = ""
        mock_settings.telegram_chat_id = "123"

        from app.core.telegram import send_alert_message
        await send_alert_message("AAPL", ConditionType.ABOVE, Decimal("150"), 160.0)

    mock_client_cls.assert_not_called()


@pytest.mark.asyncio
async def test_send_alert_no_op_when_chat_id_missing():
    """No HTTP call when telegram_chat_id is empty."""
    with (
        patch("app.core.telegram.settings") as mock_settings,
        patch("app.core.telegram.httpx.AsyncClient") as mock_client_cls,
    ):
        mock_settings.telegram_token = "some-token"
        mock_settings.telegram_chat_id = ""

        from app.core.telegram import send_alert_message
        await send_alert_message("AAPL", ConditionType.ABOVE, Decimal("150"), 160.0)

    mock_client_cls.assert_not_called()


@pytest.mark.asyncio
async def test_send_alert_posts_to_telegram():
    """Sends a POST to the Telegram Bot API when credentials are set."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.core.telegram.settings") as mock_settings,
        patch("app.core.telegram.httpx.AsyncClient", return_value=mock_client),
    ):
        mock_settings.telegram_token = "bot-token"
        mock_settings.telegram_chat_id = "chat-123"

        from app.core.telegram import send_alert_message
        await send_alert_message("AAPL", ConditionType.ABOVE, Decimal("150"), 160.0)

    mock_client.post.assert_awaited_once()
    call_kwargs = mock_client.post.call_args
    assert "sendMessage" in call_kwargs[0][0]
    payload = call_kwargs[1]["json"]
    assert payload["chat_id"] == "chat-123"
    assert "AAPL" in payload["text"]
    assert payload["parse_mode"] == "HTML"


@pytest.mark.asyncio
async def test_send_alert_message_contains_yahoo_link():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.core.telegram.settings") as mock_settings,
        patch("app.core.telegram.httpx.AsyncClient", return_value=mock_client),
    ):
        mock_settings.telegram_token = "tok"
        mock_settings.telegram_chat_id = "chat"

        from app.core.telegram import send_alert_message
        await send_alert_message("TSLA", ConditionType.BELOW, Decimal("200"), 190.0)

    payload = mock_client.post.call_args[1]["json"]
    assert "finance.yahoo.com" in payload["text"]
    assert "TSLA" in payload["text"]


@pytest.mark.asyncio
async def test_send_alert_condition_phrases():
    """Each condition type maps to the correct human-readable phrase."""
    phrases = {
        ConditionType.ABOVE: "rose above",
        ConditionType.BELOW: "fell below",
        ConditionType.EQUAL: "reached",
    }

    for condition, phrase in phrases.items():
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("app.core.telegram.settings") as mock_settings,
            patch("app.core.telegram.httpx.AsyncClient", return_value=mock_client),
        ):
            mock_settings.telegram_token = "tok"
            mock_settings.telegram_chat_id = "chat"

            from app.core.telegram import send_alert_message
            await send_alert_message("AAPL", condition, Decimal("100"), 110.0)

        payload = mock_client.post.call_args[1]["json"]
        assert phrase in payload["text"], f"Expected '{phrase}' in message for {condition}"


@pytest.mark.asyncio
async def test_send_alert_retries_on_429():
    """On HTTP 429, the function retries up to max_retries."""
    rate_limit_response = MagicMock()
    rate_limit_response.status_code = 429
    rate_limit_response.headers = {"Retry-After": "1"}

    ok_response = MagicMock()
    ok_response.status_code = 200
    ok_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=[rate_limit_response, ok_response])
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.core.telegram.settings") as mock_settings,
        patch("app.core.telegram.httpx.AsyncClient", return_value=mock_client),
        patch("app.core.telegram.asyncio.sleep", new_callable=AsyncMock),
    ):
        mock_settings.telegram_token = "tok"
        mock_settings.telegram_chat_id = "chat"

        from app.core.telegram import send_alert_message
        await send_alert_message("AAPL", ConditionType.ABOVE, Decimal("100"), 110.0)

    assert mock_client.post.await_count == 2


@pytest.mark.asyncio
async def test_send_alert_does_not_raise_on_http_error():
    """HTTP errors are logged and swallowed — no exception propagates."""
    import httpx

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(
        side_effect=httpx.HTTPStatusError("500", request=MagicMock(), response=MagicMock())
    )
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.core.telegram.settings") as mock_settings,
        patch("app.core.telegram.httpx.AsyncClient", return_value=mock_client),
    ):
        mock_settings.telegram_token = "tok"
        mock_settings.telegram_chat_id = "chat"

        from app.core.telegram import send_alert_message
        # Should not raise
        await send_alert_message("AAPL", ConditionType.ABOVE, Decimal("100"), 110.0)
