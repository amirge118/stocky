"""Unit tests for market_service.get_market_overview (FMP-based)."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.market import IndexData, MarketOverviewResponse, MoverData, SectorData
from app.services.market_service import (
    INDICES,
    SECTORS,
    TOP_MOVERS_UNIVERSE,
    get_market_overview,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _quote(symbol: str, price: float = 100.0, change_pct: float = 0.5) -> dict:
    change = price * change_pct / 100
    return {
        "symbol": symbol,
        "name": symbol,
        "price": price,
        "previousClose": price - change,
        "change": change,
        "changePercentage": change_pct,
        "volume": None,
        "marketCap": None,
    }


def _make_fmp_client(
    index_quotes: list[dict],
    sector_quotes: list[dict],
    mover_quotes: list[dict],
) -> MagicMock:
    """Mock FMP client that routes by symbol set in the URL path."""
    index_syms = set(INDICES.values())
    sector_syms = set(SECTORS.values())

    async def fake_get(path: str, params=None):
        # Each call is now a single symbol request
        sym = (params or {}).get("symbol", "")
        if sym in index_syms:
            # Return the matching index quote
            return [q for q in index_quotes if q.get("symbol") == sym]
        if sym in sector_syms:
            return [q for q in sector_quotes if q.get("symbol") == sym]
        # Mover universe
        return [q for q in mover_quotes if q.get("symbol") == sym]

    client = MagicMock()
    client.get = fake_get
    return client


# ---------------------------------------------------------------------------
# Cache hit
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cache_hit_returns_response_without_fmp():
    cached = MarketOverviewResponse(
        indices=[IndexData(symbol="^GSPC", name="S&P 500", price=4000.0, change=10.0, change_percent=0.25, sparkline=[])],
        sectors=[SectorData(name="Technology", etf="XLK", price=150.0, change_percent=0.5, news=[])],
        gainers=[MoverData(symbol="AAPL", name="AAPL", price=175.0, change_percent=1.5)],
        losers=[MoverData(symbol="TSLA", name="TSLA", price=200.0, change_percent=-1.5)],
        updated_at="2026-01-01T00:00:00+00:00",
    )
    mock_client = MagicMock()
    mock_client.get = AsyncMock()

    with (
        patch("app.services.market_service.cache_get",
              new_callable=AsyncMock, return_value=cached.model_dump(mode="json")),
        patch("app.services.market_service.get_fmp_client", return_value=mock_client),
    ):
        result = await get_market_overview()

    assert isinstance(result, MarketOverviewResponse)
    assert len(result.indices) == 1
    assert result.indices[0].symbol == "^GSPC"
    mock_client.get.assert_not_called()


# ---------------------------------------------------------------------------
# Cache miss — successful fetch
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cache_miss_fetches_all_indices():
    index_quotes = [_quote(sym, price=4000.0) for sym in INDICES.values()]
    sector_quotes = [_quote(etf, price=150.0) for etf in SECTORS.values()]
    mover_quotes = [_quote(sym, price=175.0) for sym in TOP_MOVERS_UNIVERSE]

    mock_client = _make_fmp_client(index_quotes, sector_quotes, mover_quotes)

    with (
        patch("app.services.market_service.cache_get", new_callable=AsyncMock, return_value=None),
        patch("app.services.market_service.cache_set", new_callable=AsyncMock) as mock_set,
        patch("app.services.market_service.get_fmp_client", return_value=mock_client),
    ):
        result = await get_market_overview()

    assert len(result.indices) == len(INDICES)
    assert len(result.sectors) == len(SECTORS)
    mock_set.assert_awaited_once()


@pytest.mark.asyncio
async def test_cache_miss_gainers_capped_at_five():
    mover_quotes = [_quote(sym) for sym in TOP_MOVERS_UNIVERSE]
    mock_client = _make_fmp_client([], [], mover_quotes)

    with (
        patch("app.services.market_service.cache_get", new_callable=AsyncMock, return_value=None),
        patch("app.services.market_service.cache_set", new_callable=AsyncMock),
        patch("app.services.market_service.get_fmp_client", return_value=mock_client),
    ):
        result = await get_market_overview()

    assert len(result.gainers) <= 5
    assert len(result.losers) <= 5


# ---------------------------------------------------------------------------
# Empty responses — all lists empty
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_empty_responses_yield_empty_lists():
    mock_client = _make_fmp_client([], [], [])

    with (
        patch("app.services.market_service.cache_get", new_callable=AsyncMock, return_value=None),
        patch("app.services.market_service.cache_set", new_callable=AsyncMock),
        patch("app.services.market_service.get_fmp_client", return_value=mock_client),
    ):
        result = await get_market_overview()

    assert result.indices == []
    assert result.sectors == []
    assert result.gainers == []
    assert result.losers == []


# ---------------------------------------------------------------------------
# Gainers/losers ordering
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_gainers_sorted_descending_by_change_percent():
    pcts = [1.0, 5.0, 3.0, 2.0, 4.0, 0.5, 0.1, 0.2, 0.3, 0.4]
    mover_quotes = [
        _quote(sym, price=100.0, change_pct=pcts[i % len(pcts)])
        for i, sym in enumerate(TOP_MOVERS_UNIVERSE)
    ]
    mock_client = _make_fmp_client([], [], mover_quotes)

    with (
        patch("app.services.market_service.cache_get", new_callable=AsyncMock, return_value=None),
        patch("app.services.market_service.cache_set", new_callable=AsyncMock),
        patch("app.services.market_service.get_fmp_client", return_value=mock_client),
    ):
        result = await get_market_overview()

    gainers = result.gainers
    for i in range(len(gainers) - 1):
        assert gainers[i].change_percent >= gainers[i + 1].change_percent


@pytest.mark.asyncio
async def test_losers_sorted_ascending_by_change_percent():
    pcts = [-1.0, -5.0, -3.0, -2.0, -4.0, -0.5, -0.1, -0.2, -0.3, -0.4]
    mover_quotes = [
        _quote(sym, price=100.0, change_pct=pcts[i % len(pcts)])
        for i, sym in enumerate(TOP_MOVERS_UNIVERSE)
    ]
    mock_client = _make_fmp_client([], [], mover_quotes)

    with (
        patch("app.services.market_service.cache_get", new_callable=AsyncMock, return_value=None),
        patch("app.services.market_service.cache_set", new_callable=AsyncMock),
        patch("app.services.market_service.get_fmp_client", return_value=mock_client),
    ):
        result = await get_market_overview()

    losers = result.losers
    for i in range(len(losers) - 1):
        assert losers[i].change_percent <= losers[i + 1].change_percent


# ---------------------------------------------------------------------------
# updated_at field
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_response_contains_updated_at():
    mock_client = _make_fmp_client([], [], [])

    with (
        patch("app.services.market_service.cache_get", new_callable=AsyncMock, return_value=None),
        patch("app.services.market_service.cache_set", new_callable=AsyncMock),
        patch("app.services.market_service.get_fmp_client", return_value=mock_client),
    ):
        result = await get_market_overview()

    assert result.updated_at  # non-empty string
