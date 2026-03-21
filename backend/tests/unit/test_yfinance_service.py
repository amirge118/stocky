"""Unit tests for app/services/yfinance_service.py.

Mocks:
- app.services.yfinance_service.cache_get
- app.services.yfinance_service.cache_set
- app.services.yfinance_service.asyncio.to_thread (to control the synchronous yfinance worker)
"""

from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest


# ── fetch_history_daily ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_fetch_history_daily_cache_hit():
    """Returns a dict of date→float from cache without touching yfinance."""
    cached_payload = {"2024-01-01": 150.0, "2024-01-02": 152.5}

    with (
        patch(
            "app.services.yfinance_service.cache_get",
            new_callable=AsyncMock,
            return_value=cached_payload,
        ) as mock_get,
        patch(
            "app.services.yfinance_service.cache_set",
            new_callable=AsyncMock,
        ) as mock_set,
        patch("app.services.yfinance_service.asyncio.to_thread") as mock_thread,
    ):
        from app.services.yfinance_service import fetch_history_daily

        result = await fetch_history_daily(
            "AAPL", date(2024, 1, 1), date(2024, 1, 2)
        )

    assert result == {
        date(2024, 1, 1): 150.0,
        date(2024, 1, 2): 152.5,
    }
    mock_get.assert_awaited_once()
    mock_set.assert_not_awaited()
    mock_thread.assert_not_called()


@pytest.mark.asyncio
async def test_fetch_history_daily_cache_miss_success():
    """Cache miss: calls yfinance, returns dict of date→float, stores in cache."""
    # Pre-build the expected sync result so we can bypass the real thread pool
    # (unittest.mock patches do not propagate into worker threads on Python 3.9).
    expected_result = {
        date(2024, 1, 2): 150.0,
        date(2024, 1, 3): 155.0,
    }

    async def fake_to_thread(fn, *args, **kwargs):
        return expected_result

    with (
        patch(
            "app.services.yfinance_service.cache_get",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "app.services.yfinance_service.cache_set",
            new_callable=AsyncMock,
        ) as mock_set,
        patch("app.services.yfinance_service.asyncio.to_thread", side_effect=fake_to_thread),
    ):
        from app.services.yfinance_service import fetch_history_daily

        result = await fetch_history_daily(
            "AAPL", date(2024, 1, 2), date(2024, 1, 3)
        )

    assert isinstance(result, dict)
    assert all(isinstance(k, date) for k in result)
    assert all(isinstance(v, float) for v in result.values())
    assert len(result) == 2
    mock_set.assert_awaited_once()
    # Verify cache was set with ISO-string keys
    call_args = mock_set.call_args
    cached_dict = call_args[0][1]
    assert all(isinstance(k, str) for k in cached_dict)


@pytest.mark.asyncio
async def test_fetch_history_daily_exception_returns_empty_dict():
    """asyncio.to_thread raising an exception → gracefully returns {}."""
    with (
        patch(
            "app.services.yfinance_service.cache_get",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "app.services.yfinance_service.cache_set",
            new_callable=AsyncMock,
        ) as mock_set,
        patch(
            "app.services.yfinance_service.asyncio.to_thread",
            side_effect=Exception("yfinance network error"),
        ),
    ):
        from app.services.yfinance_service import fetch_history_daily

        result = await fetch_history_daily(
            "AAPL", date(2024, 1, 1), date(2024, 1, 2)
        )

    assert result == {}
    mock_set.assert_not_awaited()


@pytest.mark.asyncio
async def test_fetch_history_daily_empty_dataframe_returns_empty_dict():
    """yfinance returns an empty DataFrame → function returns {}.

    Note: the service calls cache_set even for empty results (no early-exit guard),
    so we only assert the return value here.
    """
    async def fake_to_thread(fn, *args, **kwargs):
        return {}

    with (
        patch(
            "app.services.yfinance_service.cache_get",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "app.services.yfinance_service.cache_set",
            new_callable=AsyncMock,
        ),
        patch("app.services.yfinance_service.asyncio.to_thread", side_effect=fake_to_thread),
    ):
        from app.services.yfinance_service import fetch_history_daily

        result = await fetch_history_daily(
            "AAPL", date(2024, 1, 1), date(2024, 1, 2)
        )

    assert result == {}


# ── fetch_history_intraday ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_fetch_history_intraday_cache_hit():
    """Returns list of (datetime, float) tuples from cache."""
    cached_payload = [
        ["2024-01-01T10:00:00", 150.0],
        ["2024-01-01T10:05:00", 151.0],
    ]

    with (
        patch(
            "app.services.yfinance_service.cache_get",
            new_callable=AsyncMock,
            return_value=cached_payload,
        ) as mock_get,
        patch(
            "app.services.yfinance_service.cache_set",
            new_callable=AsyncMock,
        ) as mock_set,
        patch("app.services.yfinance_service.asyncio.to_thread") as mock_thread,
    ):
        from app.services.yfinance_service import fetch_history_intraday

        result = await fetch_history_intraday("AAPL")

    assert len(result) == 2
    assert all(isinstance(ts, datetime) for ts, _ in result)
    assert all(isinstance(price, float) for _, price in result)
    assert result[0][1] == 150.0
    assert result[1][1] == 151.0
    mock_get.assert_awaited_once()
    mock_set.assert_not_awaited()
    mock_thread.assert_not_called()


@pytest.mark.asyncio
async def test_fetch_history_intraday_cache_miss_success():
    """Cache miss: calls yfinance, returns list of (datetime, float) tuples, stores cache."""
    # Pre-build the expected sync result to bypass thread-pool patch propagation issues.
    ts1 = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    ts2 = datetime(2024, 1, 1, 10, 5, 0, tzinfo=timezone.utc)
    expected_result = [(ts1, 150.0), (ts2, 151.5)]

    async def fake_to_thread(fn, *args, **kwargs):
        return expected_result

    with (
        patch(
            "app.services.yfinance_service.cache_get",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "app.services.yfinance_service.cache_set",
            new_callable=AsyncMock,
        ) as mock_set,
        patch("app.services.yfinance_service.asyncio.to_thread", side_effect=fake_to_thread),
    ):
        from app.services.yfinance_service import fetch_history_intraday

        result = await fetch_history_intraday("AAPL")

    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(ts, datetime) for ts, _ in result)
    assert all(isinstance(p, float) for _, p in result)
    mock_set.assert_awaited_once()
    # Verify cache serialises timestamps as ISO strings
    cached_list = mock_set.call_args[0][1]
    assert all(isinstance(item[0], str) for item in cached_list)


@pytest.mark.asyncio
async def test_fetch_history_intraday_exception_returns_empty_list():
    """asyncio.to_thread raising → gracefully returns []."""
    with (
        patch(
            "app.services.yfinance_service.cache_get",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "app.services.yfinance_service.cache_set",
            new_callable=AsyncMock,
        ) as mock_set,
        patch(
            "app.services.yfinance_service.asyncio.to_thread",
            side_effect=Exception("connection timeout"),
        ),
    ):
        from app.services.yfinance_service import fetch_history_intraday

        result = await fetch_history_intraday("AAPL")

    assert result == []
    mock_set.assert_not_awaited()
