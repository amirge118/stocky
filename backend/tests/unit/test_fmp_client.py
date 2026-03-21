"""Unit tests for app/core/fmp_client.py — FMPClient.get() branch coverage."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.core.fmp_client import FMPClient, FMPError, FMPNotFoundError, FMPRateLimitError


def _make_response(status_code: int, json_data=None, json_raises=None, text=""):
    """Build a MagicMock httpx response."""
    response = MagicMock()
    response.status_code = status_code
    response.text = text
    if json_raises is not None:
        response.json.side_effect = json_raises
    elif json_data is not None:
        response.json.return_value = json_data
    response.raise_for_status = MagicMock()
    return response


# ── Status-code branches ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_raises_rate_limit_on_429():
    """HTTP 429 → FMPRateLimitError."""
    client = FMPClient(api_key="test_key")
    mock_get = AsyncMock(return_value=_make_response(429))

    with patch.object(client._client, "get", mock_get):
        with pytest.raises(FMPRateLimitError):
            await client.get("/api/v3/quote/AAPL")

    await client.aclose()


@pytest.mark.asyncio
async def test_get_raises_not_found_on_404():
    """HTTP 404 → FMPNotFoundError."""
    client = FMPClient(api_key="test_key")
    mock_get = AsyncMock(return_value=_make_response(404))

    with patch.object(client._client, "get", mock_get):
        with pytest.raises(FMPNotFoundError):
            await client.get("/api/v3/quote/UNKNOWN")

    await client.aclose()


@pytest.mark.asyncio
async def test_get_returns_empty_on_402():
    """HTTP 402 → returns [] (subscription limit)."""
    client = FMPClient(api_key="test_key")
    mock_get = AsyncMock(return_value=_make_response(402))

    with patch.object(client._client, "get", mock_get):
        result = await client.get("/api/v3/premium-endpoint")

    assert result == []
    await client.aclose()


@pytest.mark.asyncio
async def test_get_calls_raise_for_status_on_500():
    """HTTP 500 → raise_for_status() is called, propagating the error."""
    response = _make_response(500)
    response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "500 Server Error",
        request=MagicMock(),
        response=MagicMock(),
    )
    client = FMPClient(api_key="test_key")
    mock_get = AsyncMock(return_value=response)

    with patch.object(client._client, "get", mock_get):
        with pytest.raises(httpx.HTTPStatusError):
            await client.get("/api/v3/broken")

    await client.aclose()


# ── JSON / body branches ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_returns_empty_on_non_json_response():
    """Non-JSON body → returns []."""
    response = _make_response(
        200,
        json_raises=json.JSONDecodeError("err", "", 0),
        text="Premium Query Parameter required",
    )
    client = FMPClient(api_key="test_key")
    mock_get = AsyncMock(return_value=response)

    with patch.object(client._client, "get", mock_get):
        result = await client.get("/api/v3/premium")

    assert result == []
    await client.aclose()


@pytest.mark.asyncio
async def test_get_raises_fmp_error_on_api_key_error():
    """Dict with 'Error Message' containing 'api key' → FMPError."""
    response = _make_response(200, json_data={"Error Message": "Invalid API key provided"})
    client = FMPClient(api_key="test_key")
    mock_get = AsyncMock(return_value=response)

    with patch.object(client._client, "get", mock_get):
        with pytest.raises(FMPError, match="API key"):
            await client.get("/api/v3/quote/AAPL")

    await client.aclose()


@pytest.mark.asyncio
async def test_get_returns_empty_on_other_error_message():
    """Dict with 'Error Message' not about api key → returns []."""
    response = _make_response(200, json_data={"Error Message": "No data available for symbol"})
    client = FMPClient(api_key="test_key")
    mock_get = AsyncMock(return_value=response)

    with patch.object(client._client, "get", mock_get):
        result = await client.get("/api/v3/quote/XYZ")

    assert result == []
    await client.aclose()


@pytest.mark.asyncio
async def test_get_raises_rate_limit_on_limit_message():
    """Dict with 'message' containing 'limit' → FMPRateLimitError."""
    response = _make_response(
        200, json_data={"message": "You have reached the rate limit for your plan"}
    )
    client = FMPClient(api_key="test_key")
    mock_get = AsyncMock(return_value=response)

    with patch.object(client._client, "get", mock_get):
        with pytest.raises(FMPRateLimitError):
            await client.get("/api/v3/quote/AAPL")

    await client.aclose()


@pytest.mark.asyncio
async def test_get_returns_empty_on_other_message():
    """Dict with 'message' not containing 'limit' → returns []."""
    response = _make_response(200, json_data={"message": "some informational notice"})
    client = FMPClient(api_key="test_key")
    mock_get = AsyncMock(return_value=response)

    with patch.object(client._client, "get", mock_get):
        result = await client.get("/api/v3/quote/AAPL")

    assert result == []
    await client.aclose()


# ── Network-level exceptions ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_raises_fmp_error_on_timeout():
    """httpx.TimeoutException → FMPError."""
    client = FMPClient(api_key="test_key")
    mock_get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

    with patch.object(client._client, "get", mock_get):
        with pytest.raises(FMPError, match="timed out"):
            await client.get("/api/v3/quote/AAPL")

    await client.aclose()


@pytest.mark.asyncio
async def test_get_raises_fmp_error_on_connect_error():
    """httpx.ConnectError → FMPError."""
    client = FMPClient(api_key="test_key")
    mock_get = AsyncMock(side_effect=httpx.ConnectError("conn error"))

    with patch.object(client._client, "get", mock_get):
        with pytest.raises(FMPError, match="connection error"):
            await client.get("/api/v3/quote/AAPL")

    await client.aclose()


# ── Happy path ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_returns_data_on_success():
    """HTTP 200 with valid list JSON → returns parsed list."""
    payload = [{"symbol": "AAPL", "price": 182.5}]
    response = _make_response(200, json_data=payload)
    client = FMPClient(api_key="test_key")
    mock_get = AsyncMock(return_value=response)

    with patch.object(client._client, "get", mock_get):
        result = await client.get("/api/v3/quote/AAPL")

    assert result == payload
    await client.aclose()


# ── aclose ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_aclose():
    """aclose() delegates to the underlying httpx client without error."""
    client = FMPClient(api_key="test_key")
    mock_aclose = AsyncMock()

    with patch.object(client._client, "aclose", mock_aclose):
        await client.aclose()

    mock_aclose.assert_awaited_once()
