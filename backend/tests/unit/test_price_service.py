"""Unit tests for PriceService."""
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

from app.services.price_service import get_prices


def _make_multi_df(data: dict[str, list[float]]) -> pd.DataFrame:
    """Build a multi-ticker yf.download-style DataFrame (MultiIndex columns)."""
    close_data = {ticker: data[ticker] for ticker in data}
    close_df = pd.DataFrame(close_data)
    close_df.columns = pd.MultiIndex.from_tuples(
        [("Close", ticker) for ticker in close_data]
    )
    return close_df


def _make_single_df(prices: list[float]) -> pd.DataFrame:
    """Build a single-ticker yf.download-style DataFrame (flat columns)."""
    return pd.DataFrame({"Close": prices})


# ---------------------------------------------------------------------------
# Cache hit path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_all_cache_hits_skips_download():
    """When all tickers are cached, yf.download is never called."""
    cache_data = {"price:AAPL": 150.0, "price:MSFT": 300.0}

    async def fake_cache_get(key: str):
        return cache_data.get(key)

    with (
        patch("app.services.price_service.cache_get", side_effect=fake_cache_get),
        patch("app.services.price_service.cache_set", new_callable=AsyncMock),
        patch("app.services.price_service._batch_fetch_sync") as mock_dl,
    ):
        result = await get_prices(["AAPL", "MSFT"])

    assert result == {"AAPL": 150.0, "MSFT": 300.0}
    mock_dl.assert_not_called()


# ---------------------------------------------------------------------------
# Cache miss path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cache_miss_calls_download_once():
    """All misses trigger a single _batch_fetch_sync call with all missing tickers."""
    fetched = {"AAPL": 155.0, "MSFT": 310.0}

    with (
        patch("app.services.price_service.cache_get", new_callable=AsyncMock, return_value=None),
        patch("app.services.price_service.cache_set", new_callable=AsyncMock),
        patch("app.services.price_service.get_executor") as mock_executor,
        patch("asyncio.get_running_loop") as mock_loop,
    ):
        future: "asyncio.Future[dict]" = __import__("asyncio").get_event_loop().create_future()
        future.set_result(fetched)
        mock_loop.return_value.run_in_executor = MagicMock(return_value=future)
        mock_executor.return_value = MagicMock()

        result = await get_prices(["AAPL", "MSFT"])

    assert result == {"AAPL": 155.0, "MSFT": 310.0}
    call_args = mock_loop.return_value.run_in_executor.call_args
    # Second positional arg is the tickers list passed to _batch_fetch_sync
    assert set(call_args[0][2]) == {"AAPL", "MSFT"}


# ---------------------------------------------------------------------------
# Partial hit path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_partial_cache_hit():
    """Cached tickers are returned directly; only misses go to download."""
    fetched = {"MSFT": 310.0}

    async def fake_cache_get(key: str):
        return 150.0 if key == "price:AAPL" else None

    with (
        patch("app.services.price_service.cache_get", side_effect=fake_cache_get),
        patch("app.services.price_service.cache_set", new_callable=AsyncMock),
        patch("app.services.price_service.get_executor") as mock_executor,
        patch("asyncio.get_running_loop") as mock_loop,
    ):
        future = __import__("asyncio").get_event_loop().create_future()
        future.set_result(fetched)
        mock_loop.return_value.run_in_executor = MagicMock(return_value=future)
        mock_executor.return_value = MagicMock()

        result = await get_prices(["AAPL", "MSFT"])

    assert result == {"AAPL": 150.0, "MSFT": 310.0}
    # Only MSFT should have been requested
    call_args = mock_loop.return_value.run_in_executor.call_args
    assert call_args[0][2] == ["MSFT"]


# ---------------------------------------------------------------------------
# Stale fallback on exception
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_stale_fallback_on_api_error():
    """On yfinance exception, stale cache values are returned."""
    stale_prices = {"price_stale:AAPL": 148.0, "price_stale:MSFT": 298.0}

    async def fake_cache_get(key: str):
        # Fresh keys return None; stale keys return stored values
        if key.startswith("price_stale:"):
            return stale_prices.get(key)
        return None

    with (
        patch("app.services.price_service.cache_get", side_effect=fake_cache_get),
        patch("app.services.price_service.cache_set", new_callable=AsyncMock),
        patch("app.services.price_service.get_executor") as mock_executor,
        patch("asyncio.get_running_loop") as mock_loop,
    ):
        future = __import__("asyncio").get_event_loop().create_future()
        future.set_exception(RuntimeError("429 Too Many Requests"))
        mock_loop.return_value.run_in_executor = MagicMock(return_value=future)
        mock_executor.return_value = MagicMock()

        result = await get_prices(["AAPL", "MSFT"])

    assert result == {"AAPL": 148.0, "MSFT": 298.0}


@pytest.mark.asyncio
async def test_stale_fallback_partial_recovery():
    """Stale fallback returns what's available; missing tickers are omitted."""
    async def fake_cache_get(key: str):
        if key == "price_stale:AAPL":
            return 148.0
        return None  # MSFT stale also missing

    with (
        patch("app.services.price_service.cache_get", side_effect=fake_cache_get),
        patch("app.services.price_service.cache_set", new_callable=AsyncMock),
        patch("app.services.price_service.get_executor") as mock_executor,
        patch("asyncio.get_running_loop") as mock_loop,
    ):
        future = __import__("asyncio").get_event_loop().create_future()
        future.set_exception(RuntimeError("Service unavailable"))
        mock_loop.return_value.run_in_executor = MagicMock(return_value=future)
        mock_executor.return_value = MagicMock()

        result = await get_prices(["AAPL", "MSFT"])

    assert result == {"AAPL": 148.0}
    assert "MSFT" not in result


# ---------------------------------------------------------------------------
# Deduplication and uppercase
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_deduplicates_and_uppercases_tickers():
    """Duplicate and mixed-case tickers are normalised before lookup."""
    with (
        patch("app.services.price_service.cache_get", new_callable=AsyncMock, return_value=200.0),
        patch("app.services.price_service.cache_set", new_callable=AsyncMock),
        patch("app.services.price_service._batch_fetch_sync") as mock_dl,
    ):
        result = await get_prices(["aapl", "AAPL", "Aapl"])

    assert list(result.keys()) == ["AAPL"]
    mock_dl.assert_not_called()


# ---------------------------------------------------------------------------
# _batch_fetch_sync — DataFrame shape handling
# ---------------------------------------------------------------------------

def test_batch_fetch_sync_single_ticker(monkeypatch):
    """Single-ticker download returns flat DataFrame; price is extracted."""
    from app.services.price_service import _batch_fetch_sync

    df = _make_single_df([149.0, 151.0])
    monkeypatch.setattr("app.services.price_service.yf.download", lambda **kw: df)

    result = _batch_fetch_sync(["AAPL"])
    assert result == {"AAPL": 151.0}


def test_batch_fetch_sync_multi_ticker(monkeypatch):
    """Multi-ticker download returns MultiIndex DataFrame; prices extracted per ticker."""
    from app.services.price_service import _batch_fetch_sync

    df = _make_multi_df({"AAPL": [149.0, 151.0], "MSFT": [299.0, 305.0]})
    monkeypatch.setattr("app.services.price_service.yf.download", lambda **kw: df)

    result = _batch_fetch_sync(["AAPL", "MSFT"])
    assert result == {"AAPL": 151.0, "MSFT": 305.0}


def test_batch_fetch_sync_empty_df(monkeypatch):
    """Empty DataFrame returns empty dict without error."""
    from app.services.price_service import _batch_fetch_sync

    monkeypatch.setattr("app.services.price_service.yf.download", lambda **kw: pd.DataFrame())

    result = _batch_fetch_sync(["AAPL"])
    assert result == {}
