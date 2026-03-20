"""Unit tests for PriceService (FMP-based)."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.price_service import get_prices

# ---------------------------------------------------------------------------
# TASE price path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tase_price_uses_yfinance():
    """TASE symbols should use yfinance fast_info, not FMP."""
    mock_fmp = _mock_fmp([])

    with (
        patch("app.services.price_service.cache_get", new_callable=AsyncMock, return_value=None),
        patch("app.services.price_service.cache_set", new_callable=AsyncMock),
        patch("app.services.price_service.get_fmp_client", return_value=mock_fmp),
        patch("app.services.price_service.asyncio.to_thread", new_callable=AsyncMock, return_value=6.5),
    ):
        result = await get_prices(["BEZQ.TA"])

    assert result == {"BEZQ.TA": 6.5}
    # FMP client was never called for TASE symbol
    assert mock_fmp._call_log == []


@pytest.mark.asyncio
async def test_non_tase_yf_fallback_when_fmp_missing():
    """Non-TASE symbol: when FMP returns no data, fall back to yfinance."""
    mock_fmp = _mock_fmp([])  # PGY not in FMP

    with (
        patch("app.services.price_service.cache_get", new_callable=AsyncMock, return_value=None),
        patch("app.services.price_service.cache_set", new_callable=AsyncMock),
        patch("app.services.price_service.get_fmp_client", return_value=mock_fmp),
        patch("app.services.price_service.asyncio.to_thread", new_callable=AsyncMock, return_value=12.34),
    ):
        result = await get_prices(["PGY"])

    assert result == {"PGY": 12.34}


def _quote(symbol: str, price: float) -> dict:
    return {"symbol": symbol, "price": price}


def _mock_fmp(quotes: list[dict]) -> MagicMock:
    """Return a mock FMP client that routes by symbol query param."""
    quotes_by_sym = {q["symbol"]: q for q in quotes}
    call_log: list[str] = []

    async def fake_get(path: str, params=None):
        sym = (params or {}).get("symbol", "")
        call_log.append(sym)
        q = quotes_by_sym.get(sym)
        return [q] if q else []

    client = MagicMock()
    client.get = fake_get
    client._call_log = call_log
    return client


# ---------------------------------------------------------------------------
# Cache hit path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_all_cache_hits_skips_fmp():
    """When all tickers are cached, FMP client is never called."""
    cache_data = {"price:AAPL": 150.0, "price:MSFT": 300.0}

    async def fake_cache_get(key: str):
        return cache_data.get(key)

    mock_client = _mock_fmp([])
    with (
        patch("app.services.price_service.cache_get", side_effect=fake_cache_get),
        patch("app.services.price_service.cache_set", new_callable=AsyncMock),
        patch("app.services.price_service.get_fmp_client", return_value=mock_client),
    ):
        result = await get_prices(["AAPL", "MSFT"])

    assert result == {"AAPL": 150.0, "MSFT": 300.0}
    assert mock_client._call_log == []


# ---------------------------------------------------------------------------
# Cache miss path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cache_miss_calls_fmp_once():
    """All misses trigger a single FMP batch call."""
    mock_client = _mock_fmp([_quote("AAPL", 155.0), _quote("MSFT", 310.0)])

    with (
        patch("app.services.price_service.cache_get", new_callable=AsyncMock, return_value=None),
        patch("app.services.price_service.cache_set", new_callable=AsyncMock),
        patch("app.services.price_service.get_fmp_client", return_value=mock_client),
    ):
        result = await get_prices(["AAPL", "MSFT"])

    assert result == {"AAPL": 155.0, "MSFT": 310.0}
    # Two individual calls (one per symbol)
    assert len(mock_client._call_log) == 2


# ---------------------------------------------------------------------------
# Partial hit path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_partial_cache_hit():
    """Cached tickers are returned directly; only misses go to FMP."""
    mock_client = _mock_fmp([_quote("MSFT", 310.0)])

    async def fake_cache_get(key: str):
        return 150.0 if key == "price:AAPL" else None

    with (
        patch("app.services.price_service.cache_get", side_effect=fake_cache_get),
        patch("app.services.price_service.cache_set", new_callable=AsyncMock),
        patch("app.services.price_service.get_fmp_client", return_value=mock_client),
    ):
        result = await get_prices(["AAPL", "MSFT"])

    assert result == {"AAPL": 150.0, "MSFT": 310.0}


# ---------------------------------------------------------------------------
# Stale fallback on exception
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stale_fallback_on_api_error():
    """On FMP exception, stale cache values are returned."""
    stale = {"price_stale:AAPL": 148.0, "price_stale:MSFT": 298.0}

    async def fake_cache_get(key: str):
        if key.startswith("price_stale:"):
            return stale.get(key)
        return None

    mock_client = MagicMock()
    mock_client.get = AsyncMock(side_effect=RuntimeError("FMP unavailable"))

    with (
        patch("app.services.price_service.cache_get", side_effect=fake_cache_get),
        patch("app.services.price_service.cache_set", new_callable=AsyncMock),
        patch("app.services.price_service.get_fmp_client", return_value=mock_client),
    ):
        result = await get_prices(["AAPL", "MSFT"])

    assert result == {"AAPL": 148.0, "MSFT": 298.0}


@pytest.mark.asyncio
async def test_stale_fallback_partial_recovery():
    """Stale fallback returns what's available; missing tickers are omitted."""
    async def fake_cache_get(key: str):
        if key == "price_stale:AAPL":
            return 148.0
        return None

    mock_client = MagicMock()
    mock_client.get = AsyncMock(side_effect=RuntimeError("unavailable"))

    with (
        patch("app.services.price_service.cache_get", side_effect=fake_cache_get),
        patch("app.services.price_service.cache_set", new_callable=AsyncMock),
        patch("app.services.price_service.get_fmp_client", return_value=mock_client),
    ):
        result = await get_prices(["AAPL", "MSFT"])

    assert result == {"AAPL": 148.0}
    assert "MSFT" not in result


# ---------------------------------------------------------------------------
# Deduplication and uppercase
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_deduplicates_and_uppercases_tickers():
    """Duplicate and mixed-case tickers are normalised before lookup."""
    mock_client = _mock_fmp([])

    with (
        patch("app.services.price_service.cache_get", new_callable=AsyncMock, return_value=200.0),
        patch("app.services.price_service.cache_set", new_callable=AsyncMock),
        patch("app.services.price_service.get_fmp_client", return_value=mock_client),
    ):
        result = await get_prices(["aapl", "AAPL", "Aapl"])

    assert list(result.keys()) == ["AAPL"]
    assert mock_client._call_log == []


# ---------------------------------------------------------------------------
# Empty input
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_empty_tickers_returns_empty():
    mock_client = _mock_fmp([])
    with patch("app.services.price_service.get_fmp_client", return_value=mock_client):
        result = await get_prices([])
    assert result == {}
    assert mock_client._call_log == []


# ---------------------------------------------------------------------------
# Cache write on fetch
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetched_prices_written_to_fresh_and_stale_cache():
    """After a successful FMP fetch, both fresh and stale keys are written."""
    mock_client = _mock_fmp([_quote("AAPL", 155.0)])

    written_keys: list[str] = []

    async def fake_cache_set(key, value, ttl=None):
        written_keys.append(key)

    with (
        patch("app.services.price_service.cache_get", new_callable=AsyncMock, return_value=None),
        patch("app.services.price_service.cache_set", side_effect=fake_cache_set),
        patch("app.services.price_service.get_fmp_client", return_value=mock_client),
    ):
        await get_prices(["AAPL"])

    assert "price:AAPL" in written_keys
    assert "price_stale:AAPL" in written_keys
