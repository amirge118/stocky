"""Extended unit tests for app/services/stock_data.py — covers missed branches."""
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.fmp_client import FMPRateLimitError
from app.schemas.stock import (
    StockDividendsResponse,
    StockEnrichedData,
    StockHistoryResponse,
)
from app.services.stock_data import (
    _fetch_enriched_single,
    _fetch_single_quote,
    _get_cached_quote,
    _yf_history_to_response,
    _yf_quote_to_response,
    fetch_stock_data_batch,
    fetch_stock_data_from_yfinance,
    fetch_stock_dividends,
    fetch_stock_enriched_batch,
    fetch_stock_history,
    fetch_stock_info,
    fetch_stock_news,
    search_stocks_from_yfinance,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _base_fmp_quote(symbol="AAPL", price=150.0, prev=145.0, change_pct=3.45):
    return {
        "symbol": symbol,
        "companyName": f"{symbol} Corp",
        "name": f"{symbol} Corp",
        "price": price,
        "previousClose": prev,
        "change": round(price - prev, 4),
        "changePercentage": change_pct,
        "volume": 1_000_000,
        "marketCap": 2_000_000_000.0,
        "yearHigh": 200.0,
        "yearLow": 100.0,
        "avgVolume": 5_000_000,
        "pe": 25.0,
        "priceAvg50": 140.0,
        "priceAvg200": 130.0,
    }


# ---------------------------------------------------------------------------
# _yf_history_to_response — lines 53-84
# ---------------------------------------------------------------------------


def test_yf_history_to_response_skips_row_with_no_date():
    """Rows without a date field should be silently skipped (line 79)."""
    rows = [
        {"open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5, "volume": 100},  # no "date"
        {"date": "2024-01-05", "open": 10.0, "high": 11.0, "low": 9.0, "close": 10.5, "volume": 200},
    ]
    result = _yf_history_to_response("AAPL", "1m", rows)
    assert isinstance(result, StockHistoryResponse)
    assert len(result.data) == 1
    assert result.data[0].c == 10.5


def test_yf_history_to_response_skips_unparseable_date():
    """Rows with an unparseable date should be silently skipped (lines 83-84)."""
    rows = [
        {"date": "NOT-A-DATE", "open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5, "volume": 100},
        {"date": "2024-03-01", "open": 5.0, "high": 6.0, "low": 4.0, "close": 5.5, "volume": 500},
    ]
    result = _yf_history_to_response("TSLA", "1m", rows)
    assert len(result.data) == 1
    assert result.data[0].c == 5.5


def test_yf_history_to_response_empty_rows():
    """Empty row list should produce an empty data list."""
    result = _yf_history_to_response("AAPL", "1y", [])
    assert result.symbol == "AAPL"
    assert result.period == "1y"
    assert result.data == []


# ---------------------------------------------------------------------------
# _yf_quote_to_response — lines 96-114
# ---------------------------------------------------------------------------


def test_yf_quote_to_response_zero_change_computes_from_prev_close():
    """When changePercentage is absent, it should be computed from change/prev_close (lines 101-103)."""
    q = {
        "price": 100.0,
        "previousClose": 80.0,
        "change": 20.0,
        # no changePercentage
        "companyName": "Test Co",
        "volume": 999,
        "marketCap": 1_000_000.0,
        "currency": "USD",
    }
    result = _yf_quote_to_response("TEST", q)
    assert result.change_percent == round(20.0 / 80.0 * 100, 2)


def test_yf_quote_to_response_zero_prev_close_fallback():
    """When prev_close is 0 after all fallbacks, change_percent should be 0.0."""
    q = {
        "price": 0.0,
        "previousClose": 0.0,
        "change": 0.0,
        "companyName": None,
        "currency": None,
    }
    result = _yf_quote_to_response("ZERO", q)
    assert result.change_percent == 0.0
    assert result.name == "ZERO"  # falls back to sym
    assert result.currency == "USD"  # default


# ---------------------------------------------------------------------------
# _fetch_single_quote — lines 117-127
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_single_quote_fmp_success():
    """Happy path: FMP returns a quote list."""
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=[_base_fmp_quote()])
    result = await _fetch_single_quote(mock_client, "AAPL")
    assert result is not None
    assert result["symbol"] == "AAPL"


@pytest.mark.asyncio
async def test_fetch_single_quote_fmp_exception_falls_back_to_yf():
    """When FMP raises an exception, _fetch_single_quote should fall back to yf_client (lines 124-127)."""
    mock_client = MagicMock()
    mock_client.get = AsyncMock(side_effect=Exception("FMP down"))

    yf_quote = {"symbol": "AAPL", "price": 123.0}
    with patch("app.services.stock_data.yf_client.fetch_quote", new=AsyncMock(return_value=yf_quote)):
        result = await _fetch_single_quote(mock_client, "AAPL")

    assert result is not None
    assert result["price"] == 123.0


@pytest.mark.asyncio
async def test_fetch_single_quote_fmp_empty_list_falls_back_to_yf():
    """Empty FMP response should also fall back to yfinance."""
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=[])  # empty list → falls through

    yf_quote = {"symbol": "AAPL", "price": 99.0}
    with patch("app.services.stock_data.yf_client.fetch_quote", new=AsyncMock(return_value=yf_quote)):
        result = await _fetch_single_quote(mock_client, "AAPL")

    assert result["price"] == 99.0


# ---------------------------------------------------------------------------
# _get_cached_quote — lines 130-138
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_cached_quote_cache_miss_calls_fetch(monkeypatch):
    """On cache miss, _get_cached_quote should call _fetch_single_quote and cache the result (lines 134-138)."""
    mock_client = MagicMock()
    fmp_quote = _base_fmp_quote()
    mock_client.get = AsyncMock(return_value=[fmp_quote])

    cache_set_mock = AsyncMock()
    with (
        patch("app.services.stock_data.cache_get", new=AsyncMock(return_value=None)),
        patch("app.services.stock_data.cache_set", new=cache_set_mock),
    ):
        result = await _get_cached_quote(mock_client, "AAPL")

    assert result is not None
    assert result["symbol"] == "AAPL"
    cache_set_mock.assert_called_once()


@pytest.mark.asyncio
async def test_get_cached_quote_cache_hit_returns_cached():
    """On cache hit, _get_cached_quote should return cached data without calling FMP."""
    cached_quote = _base_fmp_quote()
    mock_client = MagicMock()
    mock_client.get = AsyncMock()  # should not be called

    with patch("app.services.stock_data.cache_get", new=AsyncMock(return_value=cached_quote)):
        result = await _get_cached_quote(mock_client, "AAPL")

    mock_client.get.assert_not_called()
    assert result["symbol"] == "AAPL"


# ---------------------------------------------------------------------------
# search_stocks_from_yfinance — lines 145-241
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_fmp_rate_limit_returns_warning_and_empty_fmp():
    """FMPRateLimitError during search should log warning and return [] for FMP (lines 162-164)."""
    mock_client = MagicMock()
    mock_client.get = AsyncMock(side_effect=FMPRateLimitError("rate limited"))

    with (
        patch("app.services.stock_data.cache_get", new=AsyncMock(return_value=None)),
        patch("app.services.stock_data.cache_set", new=AsyncMock()),
        patch("app.services.stock_data.get_fmp_client", return_value=mock_client),
        patch("app.services.stock_data.yf_client.search_yf", new=AsyncMock(return_value=[])),
        patch("app.services.stock_data.yf_client.search_tase", return_value=[]),
    ):
        results = await search_stocks_from_yfinance("AAPL")

    # No crash, and since all sources empty → returns []
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_search_tase_symbols_enriched_via_yf():
    """TASE symbols in search results should be enriched via yf_client.fetch_quote (lines 208-221)."""
    tase_items = [{"symbol": "BEZQ.TA", "name": "Bezeq", "exchange": "TASE", "country": "IL"}]
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=[])  # FMP returns no search results

    yf_quote = {"symbol": "BEZQ.TA", "price": 6.5, "currency": "ILS"}
    with (
        patch("app.services.stock_data.cache_get", new=AsyncMock(return_value=None)),
        patch("app.services.stock_data.cache_set", new=AsyncMock()),
        patch("app.services.stock_data.get_fmp_client", return_value=mock_client),
        patch("app.services.stock_data.yf_client.search_yf", new=AsyncMock(return_value=[])),
        patch("app.services.stock_data.yf_client.search_tase", return_value=tase_items),
        patch("app.services.stock_data.yf_client.fetch_quote", new=AsyncMock(return_value=yf_quote)),
    ):
        results = await search_stocks_from_yfinance("bezq")

    assert len(results) == 1
    assert results[0].symbol == "BEZQ.TA"
    assert results[0].current_price == 6.5


@pytest.mark.asyncio
async def test_search_generic_fmp_exception_returns_empty_fmp():
    """Generic FMP exception during search should return [] for FMP without crashing (line 166)."""
    mock_client = MagicMock()
    mock_client.get = AsyncMock(side_effect=RuntimeError("network error"))

    with (
        patch("app.services.stock_data.cache_get", new=AsyncMock(return_value=None)),
        patch("app.services.stock_data.cache_set", new=AsyncMock()),
        patch("app.services.stock_data.get_fmp_client", return_value=mock_client),
        patch("app.services.stock_data.yf_client.search_yf", new=AsyncMock(return_value=[])),
        patch("app.services.stock_data.yf_client.search_tase", return_value=[]),
    ):
        results = await search_stocks_from_yfinance("broken")

    assert isinstance(results, list)


# ---------------------------------------------------------------------------
# fetch_stock_data_from_yfinance — lines 248-314
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_stock_data_tase_path():
    """TASE symbol (.TA) should go directly to yf_client without calling FMP (lines 258-267)."""
    yf_q = {
        "symbol": "TEVA.TA",
        "companyName": "Teva",
        "price": 30.0,
        "previousClose": 29.0,
        "change": 1.0,
        "changePercentage": 3.45,
        "volume": 500_000,
        "marketCap": None,
        "currency": "ILS",
    }
    with (
        patch("app.services.stock_data.cache_get", new=AsyncMock(return_value=None)),
        patch("app.services.stock_data.cache_set", new=AsyncMock()),
        patch("app.services.stock_data.yf_client.fetch_quote", new=AsyncMock(return_value=yf_q)) as mock_yf,
        patch("app.services.stock_data.get_fmp_client") as mock_fmp,
    ):
        result = await fetch_stock_data_from_yfinance("TEVA.TA")

    mock_fmp.assert_not_called()
    mock_yf.assert_called_once_with("TEVA.TA")
    assert result.symbol == "TEVA.TA"
    assert result.current_price == 30.0


@pytest.mark.asyncio
async def test_fetch_stock_data_tase_not_found_raises_404():
    """TASE symbol not found should raise 404 (lines 260-264)."""
    from fastapi import HTTPException

    with (
        patch("app.services.stock_data.cache_get", new=AsyncMock(return_value=None)),
        patch("app.services.stock_data.cache_set", new=AsyncMock()),
        patch("app.services.stock_data.yf_client.fetch_quote", new=AsyncMock(return_value=None)),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await fetch_stock_data_from_yfinance("GHOST.TA")

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_fetch_stock_data_fmp_rate_limit_falls_back_to_yf():
    """FMPRateLimitError on _get_cached_quote should cause yfinance fallback (lines 273-274)."""
    mock_client = MagicMock()
    # _get_cached_quote internally calls _fetch_single_quote which calls client.get
    # Raise rate limit inside _fetch_single_quote to trigger q=None path
    mock_client.get = AsyncMock(side_effect=FMPRateLimitError("rate limited"))

    yf_q = {
        "symbol": "AAPL",
        "companyName": "Apple",
        "price": 155.0,
        "previousClose": 150.0,
        "change": 5.0,
        "changePercentage": 3.33,
        "volume": 1_000_000,
        "marketCap": None,
        "currency": "USD",
    }
    with (
        patch("app.services.stock_data.cache_get", new=AsyncMock(return_value=None)),
        patch("app.services.stock_data.cache_set", new=AsyncMock()),
        patch("app.services.stock_data.get_fmp_client", return_value=mock_client),
        patch("app.services.stock_data.yf_client.fetch_quote", new=AsyncMock(return_value=yf_q)),
    ):
        result = await fetch_stock_data_from_yfinance("AAPL")

    assert result.current_price == 155.0


@pytest.mark.asyncio
async def test_fetch_stock_data_fmp_price_zero_falls_back_to_yf():
    """When FMP returns price=0, should fall back to yfinance (lines 284-293)."""
    zero_quote = _base_fmp_quote(price=0.0)
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=[zero_quote])

    yf_q = {
        "symbol": "AAPL",
        "companyName": "Apple",
        "price": 155.0,
        "previousClose": 150.0,
        "change": 5.0,
        "changePercentage": 3.33,
        "volume": 1_000_000,
        "marketCap": None,
        "currency": "USD",
    }
    with (
        patch("app.services.stock_data.cache_get", new=AsyncMock(return_value=None)),
        patch("app.services.stock_data.cache_set", new=AsyncMock()),
        patch("app.services.stock_data.get_fmp_client", return_value=mock_client),
        patch("app.services.stock_data.yf_client.fetch_quote", new=AsyncMock(return_value=yf_q)),
    ):
        result = await fetch_stock_data_from_yfinance("AAPL")

    assert result.current_price == 155.0


@pytest.mark.asyncio
async def test_fetch_stock_data_generic_exception_raises_500():
    """A generic (non-rate-limit) exception should raise HTTP 500 (lines 275-279)."""
    from fastapi import HTTPException

    # We need cache_get to miss, and then _get_cached_quote to raise something
    # other than FMPRateLimitError/FMPNotFoundError
    with (
        patch("app.services.stock_data.cache_get", new=AsyncMock(return_value=None)),
        patch("app.services.stock_data.cache_set", new=AsyncMock()),
        patch(
            "app.services.stock_data._get_cached_quote",
            new=AsyncMock(side_effect=RuntimeError("unexpected")),
        ),
        patch("app.services.stock_data.get_fmp_client", return_value=MagicMock()),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await fetch_stock_data_from_yfinance("AAPL")

    assert exc_info.value.status_code == 500


# ---------------------------------------------------------------------------
# fetch_stock_data_batch — lines 321-367
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_stock_data_batch_tase_and_fmp_symbols():
    """Batch should route TASE symbols to yf and non-TASE to FMP (lines 327-365)."""
    fmp_quote = _base_fmp_quote("AAPL", price=150.0)
    yf_quote = {
        "symbol": "BEZQ.TA",
        "companyName": "Bezeq",
        "price": 6.5,
        "previousClose": 6.0,
        "change": 0.5,
        "changePercentage": 8.33,
        "volume": 100_000,
        "marketCap": None,
        "currency": "ILS",
    }
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=[fmp_quote])

    with (
        patch("app.services.stock_data.get_fmp_client", return_value=mock_client),
        patch("app.services.stock_data.yf_client.fetch_quote", new=AsyncMock(return_value=yf_quote)),
    ):
        result = await fetch_stock_data_batch(["AAPL", "BEZQ.TA"])

    assert "AAPL" in result
    assert "BEZQ.TA" in result
    assert result["AAPL"].current_price == 150.0
    assert result["BEZQ.TA"].current_price == 6.5


@pytest.mark.asyncio
async def test_fetch_stock_data_batch_skips_zero_price():
    """Batch should skip symbols with price=0 (lines 342-343, 363-364)."""
    zero_fmp = _base_fmp_quote("ZERO", price=0.0)
    zero_yf = {"symbol": "ZERO.TA", "price": 0.0}
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=[zero_fmp])

    with (
        patch("app.services.stock_data.get_fmp_client", return_value=mock_client),
        patch("app.services.stock_data.yf_client.fetch_quote", new=AsyncMock(return_value=zero_yf)),
    ):
        result = await fetch_stock_data_batch(["ZERO", "ZERO.TA"])

    assert result == {}


@pytest.mark.asyncio
async def test_fetch_stock_data_batch_skips_null_quote():
    """Batch should skip symbols where the quote is None/empty (lines 339, 361)."""
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=[])  # FMP returns empty

    with (
        patch("app.services.stock_data.get_fmp_client", return_value=mock_client),
        patch("app.services.stock_data.yf_client.fetch_quote", new=AsyncMock(return_value=None)),
    ):
        result = await fetch_stock_data_batch(["AAPL", "BEZQ.TA"])

    assert result == {}


# ---------------------------------------------------------------------------
# fetch_stock_history — lines 390-456
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_history_tase_path():
    """TASE symbol history should use yf_client.fetch_history directly (lines 399-403)."""
    rows = [
        {"date": "2024-01-05", "open": 6.0, "high": 6.5, "low": 5.9, "close": 6.3, "volume": 100_000},
    ]
    with (
        patch("app.services.stock_data.cache_get", new=AsyncMock(return_value=None)),
        patch("app.services.stock_data.cache_set", new=AsyncMock()),
        patch("app.services.stock_data.yf_client.fetch_history", new=AsyncMock(return_value=rows)) as mock_hist,
        patch("app.services.stock_data.get_fmp_client") as mock_fmp,
    ):
        result = await fetch_stock_history("BEZQ.TA", period="1m")

    mock_fmp.assert_not_called()
    mock_hist.assert_called_once_with("BEZQ.TA", "1m")
    assert result.symbol == "BEZQ.TA"
    assert len(result.data) == 1


@pytest.mark.asyncio
async def test_fetch_history_fmp_rate_limit_falls_back_to_yf():
    """FMP rate limit on history should fall back to yfinance (lines 413-427)."""
    mock_client = MagicMock()
    mock_client.get = AsyncMock(side_effect=FMPRateLimitError("rate limited"))

    rows = [
        {"date": "2024-01-05", "open": 185.0, "high": 186.0, "low": 184.0, "close": 185.5, "volume": 50_000_000},
    ]
    with (
        patch("app.services.stock_data.cache_get", new=AsyncMock(return_value=None)),
        patch("app.services.stock_data.cache_set", new=AsyncMock()),
        patch("app.services.stock_data.get_fmp_client", return_value=mock_client),
        patch("app.services.stock_data.yf_client.fetch_history", new=AsyncMock(return_value=rows)),
    ):
        result = await fetch_stock_history("AAPL", period="1m")

    assert result.symbol == "AAPL"
    assert len(result.data) == 1


@pytest.mark.asyncio
async def test_fetch_history_fmp_exception_raises_500():
    """Generic FMP exception on history should raise HTTP 500 (lines 416-420)."""
    from fastapi import HTTPException

    mock_client = MagicMock()
    mock_client.get = AsyncMock(side_effect=RuntimeError("broken"))

    with (
        patch("app.services.stock_data.cache_get", new=AsyncMock(return_value=None)),
        patch("app.services.stock_data.cache_set", new=AsyncMock()),
        patch("app.services.stock_data.get_fmp_client", return_value=mock_client),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await fetch_stock_history("AAPL", period="1m")

    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_fetch_history_fmp_returns_datetime_format():
    """FMP history with datetime format (%Y-%m-%d %H:%M:%S) should be parsed correctly (line 439)."""
    items = [
        {"date": "2024-01-05 09:30:00", "open": 184.0, "high": 185.0, "low": 183.0, "close": 184.5, "volume": 1_000_000},
        {"date": "2024-01-05 09:35:00", "open": 184.5, "high": 185.5, "low": 184.0, "close": 185.0, "volume": 900_000},
    ]
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=items)

    with (
        patch("app.services.stock_data.cache_get", new=AsyncMock(return_value=None)),
        patch("app.services.stock_data.cache_set", new=AsyncMock()),
        patch("app.services.stock_data.get_fmp_client", return_value=mock_client),
    ):
        result = await fetch_stock_history("AAPL", period="1d")

    assert result.symbol == "AAPL"
    assert len(result.data) == 2
    # FMP items are reversed (newest-first → chronological), so 09:35 becomes [0], 09:30 becomes [1]
    assert result.data[0].c == 185.0
    assert result.data[1].c == 184.5


@pytest.mark.asyncio
async def test_fetch_history_fmp_date_only_format():
    """FMP history with date-only format (%Y-%m-%d) should be parsed (line 441)."""
    items = [
        {"date": "2024-01-05", "open": 185.0, "high": 186.0, "low": 184.0, "close": 185.5, "volume": 50_000_000},
        {"date": "2024-01-04", "open": 184.0, "high": 185.0, "low": 183.0, "close": 184.0, "volume": 40_000_000},
    ]
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=items)

    with (
        patch("app.services.stock_data.cache_get", new=AsyncMock(return_value=None)),
        patch("app.services.stock_data.cache_set", new=AsyncMock()),
        patch("app.services.stock_data.get_fmp_client", return_value=mock_client),
    ):
        result = await fetch_stock_history("AAPL", period="1m")

    assert len(result.data) == 2
    # Items reversed (newest-first → chronological): Jan 4 before Jan 5
    assert result.data[0].c == 184.0
    assert result.data[1].c == 185.5


# ---------------------------------------------------------------------------
# fetch_stock_info — lines 463-589
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_stock_info_tase_path():
    """TASE symbol info should use yf_client.fetch_info directly (lines 473-499)."""
    yf_info = {
        "description": "Bezeq Israel Telecom",
        "website": "https://bezeq.co.il",
        "employees": 5000,
        "ceo": "Dudu Cohen",
        "country": "IL",
        "sector": "Communications",
        "industry": "Telecom",
        "market_cap": 1_000_000_000.0,
        "pe_ratio": 12.0,
        "forward_pe": None,
        "beta": 0.8,
        "dividend_yield": 5.0,
        "fifty_two_week_high": 7.0,
        "fifty_two_week_low": 5.0,
        "average_volume": 200_000,
    }
    with (
        patch("app.services.stock_data.cache_get", new=AsyncMock(return_value=None)),
        patch("app.services.stock_data.cache_set", new=AsyncMock()),
        patch("app.services.stock_data.yf_client.fetch_info", new=AsyncMock(return_value=yf_info)) as mock_info,
        patch("app.services.stock_data.get_fmp_client") as mock_fmp,
    ):
        result = await fetch_stock_info("BEZQ.TA")

    mock_fmp.assert_not_called()
    mock_info.assert_called_once_with("BEZQ.TA")
    assert result.symbol == "BEZQ.TA"
    assert result.sector == "Communications"
    assert result.employees == 5000


@pytest.mark.asyncio
async def test_fetch_stock_info_tase_not_found_raises_404():
    """TASE symbol info not found should raise 404 (lines 475-479)."""
    from fastapi import HTTPException

    with (
        patch("app.services.stock_data.cache_get", new=AsyncMock(return_value=None)),
        patch("app.services.stock_data.cache_set", new=AsyncMock()),
        patch("app.services.stock_data.yf_client.fetch_info", new=AsyncMock(return_value=None)),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await fetch_stock_info("GHOST.TA")

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_fetch_stock_info_fmp_empty_profile_falls_back_to_yf():
    """Empty FMP profile should trigger yfinance fallback (lines 518-540)."""
    mock_client = MagicMock()
    # profile returns empty, quote returns something
    async def fake_get(path, params=None):
        if "profile" in path:
            return []
        return [_base_fmp_quote()]

    mock_client.get = fake_get

    yf_info = {
        "description": "Apple Inc.",
        "website": "https://apple.com",
        "employees": 160_000,
        "ceo": "Tim Cook",
        "country": "US",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "market_cap": 2_500_000_000_000.0,
        "pe_ratio": 28.5,
        "forward_pe": 26.0,
        "beta": 1.2,
        "dividend_yield": 0.5,
        "fifty_two_week_high": 200.0,
        "fifty_two_week_low": 130.0,
        "average_volume": 55_000_000,
    }
    with (
        patch("app.services.stock_data.cache_get", new=AsyncMock(return_value=None)),
        patch("app.services.stock_data.cache_set", new=AsyncMock()),
        patch("app.services.stock_data.get_fmp_client", return_value=mock_client),
        patch("app.services.stock_data.yf_client.fetch_info", new=AsyncMock(return_value=yf_info)),
    ):
        result = await fetch_stock_info("AAPL")

    assert result.symbol == "AAPL"
    assert result.sector == "Technology"
    assert result.employees == 160_000


@pytest.mark.asyncio
async def test_fetch_stock_info_fmp_range_parsing():
    """FMP profile with range field should be parsed for 52W high/low when yearHigh/yearLow missing (lines 559-567)."""
    profile = [{
        "symbol": "AAPL",
        "companyName": "Apple Inc.",
        "description": "Apple.",
        "website": "https://apple.com",
        "ceo": "Tim Cook",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "country": "US",
        "fullTimeEmployees": "164000",
        "beta": 1.29,
        "mktCap": 2_750_000_000_000.0,
        "lastDiv": 0.96,
        "range": "130.0-200.0",  # range field
        "price": 155.0,
    }]
    mock_client = MagicMock()

    async def fake_get(path, params=None):
        if "profile" in path:
            return profile
        # quote: return without yearHigh/yearLow
        q = dict(_base_fmp_quote())
        del q["yearHigh"]
        del q["yearLow"]
        return [q]

    mock_client.get = fake_get

    with (
        patch("app.services.stock_data.cache_get", new=AsyncMock(return_value=None)),
        patch("app.services.stock_data.cache_set", new=AsyncMock()),
        patch("app.services.stock_data.get_fmp_client", return_value=mock_client),
    ):
        result = await fetch_stock_info("AAPL")

    assert result.fifty_two_week_low == 130.0
    assert result.fifty_two_week_high == 200.0


# ---------------------------------------------------------------------------
# fetch_stock_news — lines 596-663
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_stock_news_tase_path():
    """TASE symbol news should use yf_client.fetch_news (lines 605-619)."""
    news_raw = [
        {"title": "Bezeq profit up", "publisher": "Haaretz", "link": "https://example.com/1", "published_at": 1704412800000},
    ]
    with (
        patch("app.services.stock_data.cache_get", new=AsyncMock(return_value=None)),
        patch("app.services.stock_data.cache_set", new=AsyncMock()),
        patch("app.services.stock_data.yf_client.fetch_news", new=AsyncMock(return_value=news_raw)) as mock_news,
        patch("app.services.stock_data.get_fmp_client") as mock_fmp,
    ):
        result = await fetch_stock_news("BEZQ.TA", limit=5)

    mock_fmp.assert_not_called()
    mock_news.assert_called_once_with("BEZQ.TA", 5)
    assert len(result) == 1
    assert result[0].title == "Bezeq profit up"


@pytest.mark.asyncio
async def test_fetch_stock_news_fmp_with_published_date():
    """FMP news with publishedDate should have published_at set (lines 634-638)."""
    news = [
        {
            "title": "Apple Q4 earnings beat",
            "site": "Reuters",
            "url": "https://reuters.com/apple",
            "publishedDate": "2024-01-05 10:30:00",
        }
    ]
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=news)

    with (
        patch("app.services.stock_data.cache_get", new=AsyncMock(return_value=None)),
        patch("app.services.stock_data.cache_set", new=AsyncMock()),
        patch("app.services.stock_data.get_fmp_client", return_value=mock_client),
    ):
        result = await fetch_stock_news("AAPL", limit=5)

    assert len(result) == 1
    assert result[0].title == "Apple Q4 earnings beat"
    assert result[0].publisher == "Reuters"
    assert result[0].published_at is not None


@pytest.mark.asyncio
async def test_fetch_stock_news_fmp_empty_falls_back_to_yf():
    """FMP returning no news should fall back to yfinance (lines 648-659)."""
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=[])  # FMP returns empty

    yf_news = [
        {"title": "Apple from yfinance", "publisher": "Yahoo", "link": "https://y.com", "published_at": None},
    ]
    with (
        patch("app.services.stock_data.cache_get", new=AsyncMock(return_value=None)),
        patch("app.services.stock_data.cache_set", new=AsyncMock()),
        patch("app.services.stock_data.get_fmp_client", return_value=mock_client),
        patch("app.services.stock_data.yf_client.fetch_news", new=AsyncMock(return_value=yf_news)),
    ):
        result = await fetch_stock_news("AAPL", limit=5)

    assert len(result) == 1
    assert result[0].title == "Apple from yfinance"


# ---------------------------------------------------------------------------
# fetch_stock_dividends — lines 670-786
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_stock_dividends_tase_path():
    """TASE symbol dividends should use yf_client (lines 709-717)."""
    yf_q = {"price": 6.5}
    today = date.today()
    recent = (today - timedelta(days=100)).isoformat()
    rows = [{"date": recent, "dividend": 0.2}]

    with (
        patch("app.services.stock_data.cache_get", new=AsyncMock(return_value=None)),
        patch("app.services.stock_data.cache_set", new=AsyncMock()),
        patch("app.services.stock_data.yf_client.fetch_quote", new=AsyncMock(return_value=yf_q)),
        patch("app.services.stock_data.yf_client.fetch_dividends", new=AsyncMock(return_value=rows)),
        patch("app.services.stock_data.get_fmp_client") as mock_fmp,
    ):
        result = await fetch_stock_dividends("BEZQ.TA", years=2)

    mock_fmp.assert_not_called()
    assert result.symbol == "BEZQ.TA"
    assert result.currency == "ILS"
    assert len(result.dividends) == 1
    assert result.annual_yield is not None  # trailing sum > 0 and price > 0


@pytest.mark.asyncio
async def test_fetch_stock_dividends_fmp_empty_falls_back_to_yf():
    """FMP returning no dividends should fall back to yfinance (lines 739-746)."""
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=[])  # empty dividends

    today = date.today()
    recent = (today - timedelta(days=50)).isoformat()
    yf_rows = [{"date": recent, "dividend": 0.5}]
    yf_q = {"price": 100.0}

    with (
        patch("app.services.stock_data.cache_get", new=AsyncMock(return_value=None)),
        patch("app.services.stock_data.cache_set", new=AsyncMock()),
        patch("app.services.stock_data.get_fmp_client", return_value=mock_client),
        patch("app.services.stock_data.yf_client.fetch_dividends", new=AsyncMock(return_value=yf_rows)),
        patch("app.services.stock_data.yf_client.fetch_quote", new=AsyncMock(return_value=yf_q)),
    ):
        # _get_cached_quote also uses cache_get, mock it too via inner call
        # We also need _get_cached_quote to return something so quote_raw is a dict
        with patch("app.services.stock_data._get_cached_quote", new=AsyncMock(return_value={"price": 100.0})):
            result = await fetch_stock_dividends("AAPL", years=1)

    assert result.symbol == "AAPL"
    assert len(result.dividends) == 1


@pytest.mark.asyncio
async def test_fetch_stock_dividends_fmp_with_data_computes_annual_yield():
    """FMP returning dividend data should compute annual_yield (lines 748-785)."""
    today = date.today()
    recent1 = (today - timedelta(days=90)).isoformat()
    recent2 = (today - timedelta(days=30)).isoformat()

    dividends = [
        {"date": recent2, "dividend": 0.24, "adjDividend": 0.24},
        {"date": recent1, "dividend": 0.24, "adjDividend": 0.24},
    ]
    mock_client = MagicMock()

    async def fake_get(path, params=None):
        if "dividends" in path:
            return dividends
        return [_base_fmp_quote(price=100.0)]

    mock_client.get = fake_get

    with (
        patch("app.services.stock_data.cache_get", new=AsyncMock(return_value=None)),
        patch("app.services.stock_data.cache_set", new=AsyncMock()),
        patch("app.services.stock_data.get_fmp_client", return_value=mock_client),
        patch("app.services.stock_data._get_cached_quote", new=AsyncMock(return_value={"price": 100.0})),
    ):
        result = await fetch_stock_dividends("AAPL", years=2)

    assert isinstance(result, StockDividendsResponse)
    assert len(result.dividends) == 2
    assert result.annual_yield is not None
    assert result.annual_yield > 0


# ---------------------------------------------------------------------------
# _fetch_enriched_single — lines 793-838
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_enriched_single_fmp_data_with_week52():
    """_fetch_enriched_single should use FMP yearHigh/yearLow for non-TASE (lines 804-818)."""
    fmp_q = _base_fmp_quote()  # has yearHigh=200, yearLow=100, avgVolume=5_000_000
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=[fmp_q])

    with (
        patch("app.services.stock_data.cache_get", new=AsyncMock(return_value=None)),
        patch("app.services.stock_data.cache_set", new=AsyncMock()),
        patch("app.services.stock_data.get_fmp_client", return_value=mock_client),
        patch("app.services.stock_data.yf_client.fetch_recommendation", new=AsyncMock(return_value="buy")),
    ):
        result = await _fetch_enriched_single("AAPL")

    assert isinstance(result, StockEnrichedData)
    assert result.fifty_two_week_high == 200.0
    assert result.fifty_two_week_low == 100.0
    assert result.analyst_rating == "buy"


@pytest.mark.asyncio
async def test_fetch_enriched_single_tase_uses_yf_info():
    """TASE symbol should use yf_client.fetch_info for enrichment (lines 821-834)."""
    yf_info = {
        "fifty_two_week_high": 7.5,
        "fifty_two_week_low": 5.0,
        "average_volume": 300_000,
    }
    with (
        patch("app.services.stock_data.cache_get", new=AsyncMock(return_value=None)),
        patch("app.services.stock_data.cache_set", new=AsyncMock()),
        patch("app.services.stock_data.yf_client.fetch_info", new=AsyncMock(return_value=yf_info)),
        patch("app.services.stock_data.yf_client.fetch_recommendation", new=AsyncMock(return_value="hold")),
        patch("app.services.stock_data.get_fmp_client") as mock_fmp,
    ):
        result = await _fetch_enriched_single("BEZQ.TA")

    mock_fmp.assert_not_called()
    assert result.fifty_two_week_high == 7.5
    assert result.analyst_rating == "hold"


@pytest.mark.asyncio
async def test_fetch_enriched_single_fmp_no_data_falls_back_to_yf():
    """When FMP has no useful data, fall back to yf_client.fetch_info (lines 821-834)."""
    # FMP quote has no yearHigh/yearLow/avgVolume
    empty_fmp_q = {"symbol": "AAPL", "price": 155.0}
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=[empty_fmp_q])

    yf_info = {
        "fifty_two_week_high": 200.0,
        "fifty_two_week_low": 130.0,
        "average_volume": 55_000_000,
    }
    with (
        patch("app.services.stock_data.cache_get", new=AsyncMock(return_value=None)),
        patch("app.services.stock_data.cache_set", new=AsyncMock()),
        patch("app.services.stock_data.get_fmp_client", return_value=mock_client),
        patch("app.services.stock_data.yf_client.fetch_info", new=AsyncMock(return_value=yf_info)),
        patch("app.services.stock_data.yf_client.fetch_recommendation", new=AsyncMock(return_value="buy")),
    ):
        result = await _fetch_enriched_single("AAPL")

    assert result.fifty_two_week_high == 200.0
    assert result.avg_volume == 55_000_000


@pytest.mark.asyncio
async def test_fetch_enriched_single_yf_info_none_returns_empty():
    """When both FMP and yf_client return no data, return empty StockEnrichedData (lines 836-838)."""
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=[])  # FMP no data

    with (
        patch("app.services.stock_data.cache_get", new=AsyncMock(return_value=None)),
        patch("app.services.stock_data.cache_set", new=AsyncMock()),
        patch("app.services.stock_data.get_fmp_client", return_value=mock_client),
        patch("app.services.stock_data.yf_client.fetch_info", new=AsyncMock(return_value=None)),
        patch("app.services.stock_data.yf_client.fetch_recommendation", new=AsyncMock(return_value=None)),
    ):
        result = await _fetch_enriched_single("AAPL")

    assert result.symbol == "AAPL"
    assert result.fifty_two_week_high is None
    assert result.avg_volume is None


# ---------------------------------------------------------------------------
# fetch_stock_enriched_batch — lines 841-854
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_stock_enriched_batch_filters_exceptions():
    """fetch_stock_enriched_batch should skip symbols that raised exceptions (lines 849-853)."""
    good_result = StockEnrichedData(
        symbol="AAPL",
        fifty_two_week_high=200.0,
        fifty_two_week_low=130.0,
        avg_volume=55_000_000,
        analyst_rating="buy",
    )

    async def fake_fetch_enriched(sym):
        if sym == "AAPL":
            return good_result
        raise RuntimeError("failed for MSFT")

    with patch("app.services.stock_data._fetch_enriched_single", side_effect=fake_fetch_enriched):
        result = await fetch_stock_enriched_batch(["AAPL", "MSFT"])

    assert "AAPL" in result
    assert "MSFT" not in result
    assert result["AAPL"].fifty_two_week_high == 200.0


@pytest.mark.asyncio
async def test_fetch_stock_enriched_batch_empty():
    """Empty input should return empty dict immediately (line 846-847)."""
    result = await fetch_stock_enriched_batch([])
    assert result == {}


@pytest.mark.asyncio
async def test_fetch_stock_enriched_batch_multiple_symbols():
    """Batch should return enriched data for multiple symbols."""
    fmp_q = _base_fmp_quote()
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=[fmp_q])

    with (
        patch("app.services.stock_data.cache_get", new=AsyncMock(return_value=None)),
        patch("app.services.stock_data.cache_set", new=AsyncMock()),
        patch("app.services.stock_data.get_fmp_client", return_value=mock_client),
        patch("app.services.stock_data.yf_client.fetch_recommendation", new=AsyncMock(return_value="buy")),
    ):
        result = await fetch_stock_enriched_batch(["AAPL", "AAPL"])  # deduplication

    assert len(result) == 1
    assert "AAPL" in result
