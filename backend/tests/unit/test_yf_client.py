"""Unit tests for app/core/yf_client.py.

Mocking strategy
----------------
All public async functions delegate their synchronous yfinance work to
``asyncio.to_thread``.  Because Python 3.9 coverage does not track thread-pool
execution, and because ``unittest.mock.patch`` does not propagate into worker
threads, we intercept ``asyncio.to_thread`` *at the module level*:

    patch("app.core.yf_client.asyncio.to_thread", side_effect=fake_to_thread)

``fake_to_thread`` is an ordinary ``async def`` that accepts ``(fn, *args,
**kwargs)`` and returns whatever result we want—bypassing the real thread pool
entirely.
"""

from unittest.mock import MagicMock, patch

from app.core.yf_client import (
    _safe_float,
    fetch_dividends,
    fetch_history,
    fetch_info,
    fetch_news,
    fetch_quote,
    fetch_recommendation,
    is_tase,
    search_tase,
    search_yf,
)

# ---------------------------------------------------------------------------
# is_tase
# ---------------------------------------------------------------------------


def test_is_tase_returns_true_for_tase_symbol():
    assert is_tase("AAPL.TA") is True


def test_is_tase_returns_false_for_non_tase():
    assert is_tase("AAPL") is False


def test_is_tase_case_insensitive():
    assert is_tase("aapl.ta") is True


# ---------------------------------------------------------------------------
# search_tase
# ---------------------------------------------------------------------------


def test_search_tase_finds_by_symbol():
    results = search_tase("BEZQ")
    symbols = [r["symbol"] for r in results]
    assert "BEZQ.TA" in symbols


def test_search_tase_finds_by_name():
    results = search_tase("Bezeq")
    assert len(results) >= 1
    names = [r["name"] for r in results]
    assert any("Bezeq" in name for name in names)


def test_search_tase_respects_limit():
    results = search_tase("a", limit=2)
    assert len(results) <= 2


def test_search_tase_no_match_returns_empty():
    results = search_tase("XYZNOTEXIST")
    assert results == []


# ---------------------------------------------------------------------------
# _safe_float
# ---------------------------------------------------------------------------


def test_safe_float_converts_int():
    assert _safe_float(150) == 150.0


def test_safe_float_none_returns_none():
    assert _safe_float(None) is None


def test_safe_float_nan_returns_none():
    assert _safe_float(float("nan")) is None


def test_safe_float_invalid_string_returns_none():
    assert _safe_float("not_a_number") is None


# ---------------------------------------------------------------------------
# search_yf (async)
# ---------------------------------------------------------------------------


async def test_search_yf_returns_results():
    fake_results = [
        {
            "symbol": "AAPL",
            "name": "Apple",
            "stockExchange": "NMS",
            "exchangeShortName": "NMS",
            "currency": None,
            "country": None,
        }
    ]

    async def fake_to_thread(fn, *args, **kwargs):
        return fake_results

    with patch("app.core.yf_client.asyncio.to_thread", side_effect=fake_to_thread):
        result = await search_yf("Apple")

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["symbol"] == "AAPL"


async def test_search_yf_exception_returns_empty():
    """search_yf's _sync closure catches its own exceptions and returns [].

    We simulate this by having fake_to_thread actually invoke fn() after
    patching yfinance so that yf.Search raises inside the closure.
    """
    import yfinance as yf

    async def fake_to_thread(fn, *args, **kwargs):
        return fn(*args, **kwargs)

    with (
        patch("app.core.yf_client.asyncio.to_thread", side_effect=fake_to_thread),
        patch.object(yf, "Search", side_effect=Exception("network failure")),
    ):
        result = await search_yf("Apple")

    assert result == []


# ---------------------------------------------------------------------------
# fetch_quote (async)
# ---------------------------------------------------------------------------


async def test_fetch_quote_success():
    expected = {
        "price": 150.0,
        "previousClose": 145.0,
        "change": 5.0,
        "changePercentage": 3.45,
        "volume": None,
        "marketCap": None,
        "currency": "USD",
        "companyName": "AAPL",
    }

    async def fake_to_thread(fn, *args, **kwargs):
        return expected

    with patch("app.core.yf_client.asyncio.to_thread", side_effect=fake_to_thread):
        result = await fetch_quote("AAPL")

    assert result == expected


async def test_fetch_quote_returns_none_when_price_missing():
    async def fake_to_thread(fn, *args, **kwargs):
        return None

    with patch("app.core.yf_client.asyncio.to_thread", side_effect=fake_to_thread):
        result = await fetch_quote("AAPL")

    assert result is None


# ---------------------------------------------------------------------------
# fetch_info (async)
# ---------------------------------------------------------------------------


async def test_fetch_info_success():
    expected = {
        "description": "Apple Inc. designs and sells electronics.",
        "website": "https://apple.com",
        "employees": 160000,
        "ceo": "Tim Cook",
        "country": "United States",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "market_cap": 2_800_000_000_000.0,
        "pe_ratio": 28.5,
        "forward_pe": 25.0,
        "beta": 1.2,
        "dividend_yield": 0.55,
        "fifty_two_week_high": 200.0,
        "fifty_two_week_low": 120.0,
        "average_volume": 60_000_000,
    }

    async def fake_to_thread(fn, *args, **kwargs):
        return expected

    with patch("app.core.yf_client.asyncio.to_thread", side_effect=fake_to_thread):
        result = await fetch_info("AAPL")

    assert result == expected


async def test_fetch_info_failure_returns_none():
    async def fake_to_thread(fn, *args, **kwargs):
        return None

    with patch("app.core.yf_client.asyncio.to_thread", side_effect=fake_to_thread):
        result = await fetch_info("AAPL")

    assert result is None


# ---------------------------------------------------------------------------
# fetch_history (async)
# ---------------------------------------------------------------------------


async def test_fetch_history_success():
    expected = [
        {
            "date": "2024-01-02T00:00:00",
            "open": 150.0,
            "high": 155.0,
            "low": 148.0,
            "close": 152.0,
            "volume": 1_000_000,
        }
    ]

    async def fake_to_thread(fn, *args, **kwargs):
        return expected

    with patch("app.core.yf_client.asyncio.to_thread", side_effect=fake_to_thread):
        result = await fetch_history("AAPL", period="1m")

    assert result == expected


async def test_fetch_history_empty_returns_empty():
    async def fake_to_thread(fn, *args, **kwargs):
        return []

    with patch("app.core.yf_client.asyncio.to_thread", side_effect=fake_to_thread):
        result = await fetch_history("AAPL", period="1m")

    assert result == []


async def test_fetch_history_uses_period_map_default():
    """Calling fetch_history with the default period must not raise."""

    async def fake_to_thread(fn, *args, **kwargs):
        return []

    with patch("app.core.yf_client.asyncio.to_thread", side_effect=fake_to_thread):
        result = await fetch_history("AAPL")

    assert isinstance(result, list)


# ---------------------------------------------------------------------------
# fetch_news (async)
# ---------------------------------------------------------------------------


async def test_fetch_news_success():
    expected = [
        {
            "title": "Test",
            "publisher": "Reuters",
            "link": "http://example.com",
            "published_at": 1_234_567_890_000,
        }
    ]

    async def fake_to_thread(fn, *args, **kwargs):
        return expected

    with patch("app.core.yf_client.asyncio.to_thread", side_effect=fake_to_thread):
        result = await fetch_news("AAPL")

    assert result == expected


async def test_fetch_news_empty_returns_empty():
    async def fake_to_thread(fn, *args, **kwargs):
        return []

    with patch("app.core.yf_client.asyncio.to_thread", side_effect=fake_to_thread):
        result = await fetch_news("AAPL")

    assert result == []


# ---------------------------------------------------------------------------
# fetch_recommendation (async)
# ---------------------------------------------------------------------------


async def test_fetch_recommendation_success():
    async def fake_to_thread(fn, *args, **kwargs):
        return "buy"

    with patch("app.core.yf_client.asyncio.to_thread", side_effect=fake_to_thread):
        result = await fetch_recommendation("AAPL")

    assert result == "buy"


async def test_fetch_recommendation_none_when_unavailable():
    async def fake_to_thread(fn, *args, **kwargs):
        return None

    with patch("app.core.yf_client.asyncio.to_thread", side_effect=fake_to_thread):
        result = await fetch_recommendation("AAPL")

    assert result is None


# ---------------------------------------------------------------------------
# fetch_dividends (async)
# ---------------------------------------------------------------------------


async def test_fetch_dividends_success():
    expected = [{"date": "2024-01-15", "dividend": 0.25}]

    async def fake_to_thread(fn, *args, **kwargs):
        return expected

    with patch("app.core.yf_client.asyncio.to_thread", side_effect=fake_to_thread):
        result = await fetch_dividends("AAPL")

    assert result == expected


async def test_fetch_dividends_empty_returns_empty():
    async def fake_to_thread(fn, *args, **kwargs):
        return []

    with patch("app.core.yf_client.asyncio.to_thread", side_effect=fake_to_thread):
        result = await fetch_dividends("AAPL")

    assert result == []


# ---------------------------------------------------------------------------
# Inner _sync() function coverage tests
# These tests call fn(*args, **kwargs) via side_effect so the inner closures
# are actually executed, covering the lines previously left uncovered.
# ---------------------------------------------------------------------------


async def test_fetch_quote_inner_function_success():
    """Covers inner _sync() execution path of fetch_quote."""
    mock_fi = MagicMock()
    mock_fi.last_price = 150.0
    mock_fi.previous_close = 145.0
    mock_fi.currency = "USD"
    mock_fi.three_month_average_volume = 1_000_000.0
    mock_fi.market_cap = 2e12

    mock_ticker = MagicMock()
    mock_ticker.fast_info = mock_fi

    async def call_fn(fn, *a, **kw):
        return fn(*a, **kw)

    with patch("app.core.yf_client.yf.Ticker", return_value=mock_ticker):
        with patch("app.core.yf_client.asyncio.to_thread", side_effect=call_fn):
            result = await fetch_quote("AAPL")

    assert result is not None
    assert result["price"] == 150.0
    assert result["currency"] == "USD"


async def test_fetch_quote_inner_function_no_price_returns_none():
    mock_fi = MagicMock()
    mock_fi.last_price = None  # _safe_float(None) = None
    mock_ticker = MagicMock()
    mock_ticker.fast_info = mock_fi

    async def call_fn(fn, *a, **kw):
        return fn(*a, **kw)

    with patch("app.core.yf_client.yf.Ticker", return_value=mock_ticker):
        with patch("app.core.yf_client.asyncio.to_thread", side_effect=call_fn):
            result = await fetch_quote("AAPL")

    assert result is None


async def test_fetch_info_inner_function_success():
    raw = {
        "longBusinessSummary": "Apple is a tech company",
        "website": "https://apple.com",
        "fullTimeEmployees": 160000,
        "country": "USA",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "marketCap": 2_500_000_000_000,
        "trailingPE": 28.5,
        "forwardPE": 25.0,
        "beta": 1.2,
        "currentPrice": 150.0,
        "lastDividendValue": 0.96,
        "fiftyTwoWeekHigh": 200.0,
        "fiftyTwoWeekLow": 120.0,
        "averageVolume": 80_000_000,
        "companyOfficers": [{"title": "CEO", "name": "Tim Cook"}],
    }
    mock_ticker = MagicMock()
    mock_ticker.info = raw

    async def call_fn(fn, *a, **kw):
        return fn(*a, **kw)

    with patch("app.core.yf_client.yf.Ticker", return_value=mock_ticker):
        with patch("app.core.yf_client.asyncio.to_thread", side_effect=call_fn):
            result = await fetch_info("AAPL")

    assert result is not None
    assert result["sector"] == "Technology"
    assert result["ceo"] == "Tim Cook"


async def test_fetch_history_inner_function_success():
    import pandas as pd

    idx = pd.DatetimeIndex(["2024-01-02T10:00:00"])
    df = pd.DataFrame(
        {"Open": [149.0], "High": [152.0], "Low": [148.0], "Close": [151.0], "Volume": [1_000_000]},
        index=idx,
    )
    mock_ticker = MagicMock()
    mock_ticker.history.return_value = df

    async def call_fn(fn, *a, **kw):
        return fn(*a, **kw)

    with patch("app.core.yf_client.yf.Ticker", return_value=mock_ticker):
        with patch("app.core.yf_client.asyncio.to_thread", side_effect=call_fn):
            result = await fetch_history("AAPL", "1m")

    assert len(result) == 1
    assert result[0]["close"] == 151.0
    assert result[0]["volume"] == 1_000_000


async def test_fetch_news_inner_function_success():
    news_item = {
        "content": {
            "title": "Apple announces new product",
            "pubDate": "2024-01-02T10:00:00",
            "provider": {"displayName": "Reuters"},
            "canonicalUrl": {"url": "https://reuters.com/article"},
        }
    }
    mock_ticker = MagicMock()
    mock_ticker.news = [news_item]

    async def call_fn(fn, *a, **kw):
        return fn(*a, **kw)

    with patch("app.core.yf_client.yf.Ticker", return_value=mock_ticker):
        with patch("app.core.yf_client.asyncio.to_thread", side_effect=call_fn):
            result = await fetch_news("AAPL")

    assert len(result) == 1
    assert result[0]["title"] == "Apple announces new product"
    assert result[0]["publisher"] == "Reuters"


async def test_fetch_recommendation_inner_function_success():
    mock_ticker = MagicMock()
    mock_ticker.info = {"recommendationKey": "buy"}

    async def call_fn(fn, *a, **kw):
        return fn(*a, **kw)

    with patch("app.core.yf_client.yf.Ticker", return_value=mock_ticker):
        with patch("app.core.yf_client.asyncio.to_thread", side_effect=call_fn):
            result = await fetch_recommendation("AAPL")

    assert result == "buy"


async def test_fetch_dividends_inner_function_success():
    import pandas as pd

    idx = pd.DatetimeIndex(["2024-01-15"])
    series = pd.Series([0.25], index=idx)
    mock_ticker = MagicMock()
    mock_ticker.dividends = series

    async def call_fn(fn, *a, **kw):
        return fn(*a, **kw)

    with patch("app.core.yf_client.yf.Ticker", return_value=mock_ticker):
        with patch("app.core.yf_client.asyncio.to_thread", side_effect=call_fn):
            result = await fetch_dividends("AAPL")

    assert len(result) == 1
    assert result[0]["dividend"] == 0.25


async def test_search_yf_inner_function_returns_filtered_results():
    import yfinance as yf

    mock_search = MagicMock()
    mock_search.quotes = [
        {"symbol": "AAPL", "longname": "Apple Inc.", "exchDisp": "NASDAQ", "exchange": "NMS", "quoteType": "EQUITY"},
        {"symbol": "BTC-USD", "longname": "Bitcoin USD", "exchange": "CCC", "quoteType": "CRYPTOCURRENCY"},  # should be excluded
    ]

    async def call_fn(fn, *a, **kw):
        return fn(*a, **kw)

    with patch.object(yf, "Search", return_value=mock_search, create=True):
        with patch("app.core.yf_client.asyncio.to_thread", side_effect=call_fn):
            result = await search_yf("AAPL")

    assert len(result) == 1
    assert result[0]["symbol"] == "AAPL"
