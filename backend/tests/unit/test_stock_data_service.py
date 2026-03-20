"""Unit tests for stock_data service (FMP-based)."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.stock import (
    StockDataResponse,
    StockHistoryResponse,
    StockInfoResponse,
    StockSearchResult,
)
from app.core.fmp_client import FMPRateLimitError
from app.services.stock_data import (
    fetch_stock_data_batch,
    fetch_stock_data_from_yfinance,
    fetch_stock_history,
    fetch_stock_info,
    fetch_stock_news,
    search_stocks_from_yfinance,
)


def _fmp_quote(
    symbol: str = "AAPL",
    price: float = 155.0,
    prev: float = 150.0,
    change_pct: float = 3.33,
) -> dict:
    return {
        "symbol": symbol,
        "name": "Apple Inc.",
        "price": price,
        "previousClose": prev,
        "change": price - prev,
        "changePercentage": change_pct,
        "volume": 1000000,
        "marketCap": 2500000000000.0,
        "yearHigh": 200.0,
        "yearLow": 130.0,
        "avgVolume": 55000000,
        "pe": 28.5,
        "priceAvg50": 150.0,
        "priceAvg200": 145.0,
    }


def _mock_fmp(**responses: object) -> MagicMock:
    """
    Build a mock FMP client. Pass keyword args like:
        quote=[{...}], profile=[{...}]
    The mock routes by checking the URL path and symbol param.
    """
    all_quotes: list[dict] = responses.get("quote", [])  # type: ignore[assignment]
    quotes_by_sym = {q["symbol"]: q for q in all_quotes}

    async def fake_get(path: str, params=None):
        sym = (params or {}).get("symbol", "")
        if "stock-news" in path:
            return responses.get("news", [])
        if "dividends" in path:
            return responses.get("dividends", [])
        if "profile" in path:
            profile_data = responses.get("profile", [])
            if profile_data:
                # Merge quote fields into profile so both price and info are available
                # (real FMP /stable/profile returns combined data)
                quote_for_sym = quotes_by_sym.get(sym) or (all_quotes[0] if all_quotes else None)
                if quote_for_sym:
                    merged = {**quote_for_sym, **profile_data[0]}
                    return [merged]
                return profile_data
            # Fall back to quotes when no explicit profile data provided
            # (/stable/profile is also used for live-quote lookups)
            if sym and sym in quotes_by_sym:
                return [quotes_by_sym[sym]]
            return all_quotes
        if "historical-price-eod" in path or "intraday" in path:
            return responses.get("historical", [])
        if "search" in path:
            return responses.get("search", [])
        # Quote: return matching symbol or all quotes (for single-symbol callers)
        if sym and sym in quotes_by_sym:
            return [quotes_by_sym[sym]]
        return all_quotes

    client = MagicMock()
    client.get = fake_get
    return client


# ---------------------------------------------------------------------------
# fetch_stock_data_from_yfinance
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_stock_data_returns_data():
    mock_client = _mock_fmp(quote=[_fmp_quote()])

    with (
        patch("app.services.stock_data.cache_get", new_callable=AsyncMock, return_value=None),
        patch("app.services.stock_data.cache_set", new_callable=AsyncMock),
        patch("app.services.stock_data.get_fmp_client", return_value=mock_client),
    ):
        result = await fetch_stock_data_from_yfinance("AAPL")

    assert isinstance(result, StockDataResponse)
    assert result.symbol == "AAPL"
    assert result.current_price == 155.0
    assert result.previous_close == 150.0
    assert result.volume == 1000000


@pytest.mark.asyncio
async def test_fetch_stock_data_cache_hit():
    cached = _fmp_quote()
    cached_response = StockDataResponse(
        symbol="AAPL", name="Apple Inc.", current_price=155.0,
        previous_close=150.0, change=5.0, change_percent=3.33,
        volume=None, market_cap=None, currency="USD",
    )

    with patch(
        "app.services.stock_data.cache_get",
        new_callable=AsyncMock,
        return_value=cached_response.model_dump(mode="json"),
    ):
        result = await fetch_stock_data_from_yfinance("AAPL")

    assert result.symbol == "AAPL"
    assert result.current_price == 155.0


@pytest.mark.asyncio
async def test_fetch_stock_data_not_found_raises_404():
    from fastapi import HTTPException

    mock_client = _mock_fmp(quote=[])  # FMP returns empty → 404

    with (
        patch("app.services.stock_data.cache_get", new_callable=AsyncMock, return_value=None),
        patch("app.services.stock_data.cache_set", new_callable=AsyncMock),
        patch("app.services.stock_data.get_fmp_client", return_value=mock_client),
        patch("app.services.stock_data.yf_client.fetch_quote", new_callable=AsyncMock, return_value=None),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await fetch_stock_data_from_yfinance("INVALID")

    assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# fetch_stock_data_batch
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_stock_data_batch_multiple_symbols():
    quotes = [_fmp_quote("AAPL", 155.0), _fmp_quote("MSFT", 310.0)]
    mock_client = _mock_fmp(quote=quotes)

    with patch("app.services.stock_data.get_fmp_client", return_value=mock_client):
        result = await fetch_stock_data_batch(["AAPL", "MSFT"])

    assert set(result.keys()) == {"AAPL", "MSFT"}
    assert result["AAPL"].current_price == 155.0
    assert result["MSFT"].current_price == 310.0


@pytest.mark.asyncio
async def test_fetch_stock_data_batch_empty_input():
    result = await fetch_stock_data_batch([])
    assert result == {}


@pytest.mark.asyncio
async def test_fetch_stock_data_batch_deduplicates():
    mock_client = _mock_fmp(quote=[_fmp_quote("AAPL", 155.0)])

    with patch("app.services.stock_data.get_fmp_client", return_value=mock_client):
        result = await fetch_stock_data_batch(["AAPL", "aapl", "AAPL"])

    assert list(result.keys()) == ["AAPL"]


# ---------------------------------------------------------------------------
# search_stocks_from_yfinance
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_returns_results():
    search_items = [
        {"symbol": "AAPL", "name": "Apple Inc.", "currency": "USD",
         "stockExchange": "NASDAQ", "exchangeShortName": "NASDAQ"},
    ]
    mock_client = _mock_fmp(search=search_items, quote=[_fmp_quote()])

    with (
        patch("app.services.stock_data.cache_get", new_callable=AsyncMock, return_value=None),
        patch("app.services.stock_data.cache_set", new_callable=AsyncMock),
        patch("app.services.stock_data.get_fmp_client", return_value=mock_client),
        patch("app.services.stock_data.yf_client.search_yf", new_callable=AsyncMock, return_value=[]),
    ):
        results = await search_stocks_from_yfinance("AAPL")

    assert len(results) == 1
    assert results[0].symbol == "AAPL"
    assert results[0].name == "Apple Inc."
    assert results[0].current_price == 155.0


@pytest.mark.asyncio
async def test_search_empty_query_returns_empty():
    mock_client = _mock_fmp(search=[])

    with (
        patch("app.services.stock_data.cache_get", new_callable=AsyncMock, return_value=None),
        patch("app.services.stock_data.cache_set", new_callable=AsyncMock),
        patch("app.services.stock_data.get_fmp_client", return_value=mock_client),
        patch("app.services.stock_data.yf_client.search_yf", new_callable=AsyncMock, return_value=[]),
    ):
        results = await search_stocks_from_yfinance("XYZNOTEXIST")

    assert results == []


# ---------------------------------------------------------------------------
# TASE routing tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_stock_data_tase_uses_yfinance():
    """BEZQ.TA should call yf_client.fetch_quote, not FMP."""
    yf_q = {
        "symbol": "BEZQ.TA", "companyName": "Bezeq", "price": 6.5,
        "previousClose": 6.3, "change": 0.2, "changePercentage": 3.17,
        "volume": 1000000, "marketCap": None, "currency": "ILS",
    }

    with (
        patch("app.services.stock_data.cache_get", new_callable=AsyncMock, return_value=None),
        patch("app.services.stock_data.cache_set", new_callable=AsyncMock),
        patch("app.services.stock_data.yf_client.fetch_quote", new_callable=AsyncMock, return_value=yf_q) as mock_yf,
        patch("app.services.stock_data.get_fmp_client") as mock_fmp,
    ):
        result = await fetch_stock_data_from_yfinance("BEZQ.TA")

    mock_yf.assert_called_once_with("BEZQ.TA")
    mock_fmp.assert_not_called()
    assert result.symbol == "BEZQ.TA"
    assert result.current_price == 6.5


@pytest.mark.asyncio
async def test_fetch_history_tase_uses_yfinance():
    """BEZQ.TA history should call yf_client.fetch_history, not FMP."""
    rows = [
        {"date": "2024-01-04", "open": 6.0, "high": 6.5, "low": 5.9, "close": 6.3, "volume": 500000},
    ]

    with (
        patch("app.services.stock_data.cache_get", new_callable=AsyncMock, return_value=None),
        patch("app.services.stock_data.cache_set", new_callable=AsyncMock),
        patch("app.services.stock_data.yf_client.fetch_history", new_callable=AsyncMock, return_value=rows) as mock_hist,
        patch("app.services.stock_data.get_fmp_client") as mock_fmp,
    ):
        result = await fetch_stock_history("BEZQ.TA", period="1m")

    mock_hist.assert_called_once_with("BEZQ.TA", "1m")
    mock_fmp.assert_not_called()
    assert result.symbol == "BEZQ.TA"
    assert len(result.data) == 1


@pytest.mark.asyncio
async def test_search_tase_symbol_appears_first():
    """TASE results from search_tase should appear before FMP results."""
    fmp_items = [
        {"symbol": "TEVA", "name": "Teva Pharma US", "currency": "USD",
         "stockExchange": "NYSE", "exchangeShortName": "NYSE"},
    ]
    tase_items = [
        {"symbol": "TEVA.TA", "name": "Teva Pharmaceutical", "exchange": "TASE", "country": "IL"},
    ]
    mock_client = _mock_fmp(search=fmp_items, quote=[_fmp_quote("TEVA", 15.0)])

    with (
        patch("app.services.stock_data.cache_get", new_callable=AsyncMock, return_value=None),
        patch("app.services.stock_data.cache_set", new_callable=AsyncMock),
        patch("app.services.stock_data.get_fmp_client", return_value=mock_client),
        patch("app.services.stock_data.yf_client.search_yf", new_callable=AsyncMock, return_value=[]),
        patch("app.services.stock_data.yf_client.search_tase", return_value=tase_items),
        patch("app.services.stock_data.yf_client.fetch_quote", new_callable=AsyncMock, return_value={"price": 6.5}),
    ):
        results = await search_stocks_from_yfinance("teva")

    assert results[0].symbol == "TEVA.TA"
    assert any(r.symbol == "TEVA" for r in results)


# ---------------------------------------------------------------------------
# fetch_stock_history
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_history_daily():
    historical = [
        {"date": "2024-01-05", "open": 185.0, "high": 186.0, "low": 184.0, "close": 185.5, "volume": 50000000},
        {"date": "2024-01-04", "open": 184.0, "high": 185.0, "low": 183.0, "close": 184.0, "volume": 40000000},
    ]
    mock_client = _mock_fmp(historical=historical)

    with (
        patch("app.services.stock_data.cache_get", new_callable=AsyncMock, return_value=None),
        patch("app.services.stock_data.cache_set", new_callable=AsyncMock),
        patch("app.services.stock_data.get_fmp_client", return_value=mock_client),
    ):
        result = await fetch_stock_history("AAPL", period="1m")

    assert isinstance(result, StockHistoryResponse)
    assert result.symbol == "AAPL"
    assert result.period == "1m"
    # Historical reversed to chronological: Jan 4 comes before Jan 5
    assert len(result.data) == 2
    assert result.data[0].c == 184.0
    assert result.data[1].c == 185.5


@pytest.mark.asyncio
async def test_fetch_history_intraday_1d():
    items = [
        {"date": "2024-01-05 09:35:00", "open": 185.0, "high": 185.5, "low": 184.8, "close": 185.2, "volume": 500000},
        {"date": "2024-01-05 09:30:00", "open": 184.8, "high": 185.1, "low": 184.5, "close": 185.0, "volume": 400000},
    ]
    mock_client = _mock_fmp(historical=items)

    with (
        patch("app.services.stock_data.cache_get", new_callable=AsyncMock, return_value=None),
        patch("app.services.stock_data.cache_set", new_callable=AsyncMock),
        patch("app.services.stock_data.get_fmp_client", return_value=mock_client),
    ):
        result = await fetch_stock_history("AAPL", period="1d")

    assert len(result.data) == 2
    # Reversed to chronological: 09:30 before 09:35
    assert result.data[0].c == 185.0
    assert result.data[1].c == 185.2


# ---------------------------------------------------------------------------
# fetch_stock_info
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_stock_info_combines_profile_and_quote():
    profile = [{
        "symbol": "AAPL",
        "companyName": "Apple Inc.",
        "description": "Apple makes iPhones.",
        "website": "https://apple.com",
        "ceo": "Tim Cook",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "country": "US",
        "fullTimeEmployees": "164000",
        "beta": 1.29,
        "mktCap": 2750000000000.0,
        "lastDiv": 0.96,
    }]
    quote = [_fmp_quote()]
    mock_client = _mock_fmp(profile=profile, quote=quote)

    with (
        patch("app.services.stock_data.cache_get", new_callable=AsyncMock, return_value=None),
        patch("app.services.stock_data.cache_set", new_callable=AsyncMock),
        patch("app.services.stock_data.get_fmp_client", return_value=mock_client),
    ):
        result = await fetch_stock_info("AAPL")

    assert isinstance(result, StockInfoResponse)
    assert result.symbol == "AAPL"
    assert result.ceo == "Tim Cook"
    assert result.sector == "Technology"
    assert result.employees == 164000
    assert result.pe_ratio == 28.5
    assert result.average_volume == 55000000


# ---------------------------------------------------------------------------
# fetch_stock_news
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_news_returns_items():
    news = [
        {"title": "Apple hits record high", "site": "Reuters",
         "url": "https://example.com/1", "publishedDate": "2024-01-05 10:00:00"},
        {"title": "iPhone sales strong", "site": "Bloomberg",
         "url": "https://example.com/2", "publishedDate": "2024-01-04 09:00:00"},
    ]
    mock_client = _mock_fmp(news=news)

    with (
        patch("app.services.stock_data.cache_get", new_callable=AsyncMock, return_value=None),
        patch("app.services.stock_data.cache_set", new_callable=AsyncMock),
        patch("app.services.stock_data.get_fmp_client", return_value=mock_client),
    ):
        result = await fetch_stock_news("AAPL", limit=5)

    assert len(result) == 2
    assert result[0].title == "Apple hits record high"
    assert result[0].publisher == "Reuters"
    assert result[0].published_at is not None


@pytest.mark.asyncio
async def test_fetch_news_empty_on_failure():
    mock_client = MagicMock()
    mock_client.get = AsyncMock(side_effect=Exception("FMP error"))

    with (
        patch("app.services.stock_data.cache_get", new_callable=AsyncMock, return_value=None),
        patch("app.services.stock_data.get_fmp_client", return_value=mock_client),
    ):
        result = await fetch_stock_news("AAPL")

    assert result == []


# ---------------------------------------------------------------------------
# search_stocks_from_yfinance — FMP rate-limit graceful degradation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_fmp_rate_limit_falls_back_to_yfinance():
    """When FMP is rate-limited, search should return yfinance results instead of 503."""
    mock_fmp_client = MagicMock()
    mock_fmp_client.get = AsyncMock(side_effect=FMPRateLimitError("rate limit"))

    hims_result = {
        "symbol": "HIMS",
        "shortname": "Hims & Hers Health",
        "exchange": "NYSE",
        "quoteType": "EQUITY",
    }
    mock_yf_client = MagicMock()
    mock_yf_client.search_yf = AsyncMock(return_value=[hims_result])
    mock_yf_client.search_tase = MagicMock(return_value=[])

    with (
        patch("app.services.stock_data.cache_get", new_callable=AsyncMock, return_value=None),
        patch("app.services.stock_data.cache_set", new_callable=AsyncMock),
        patch("app.services.stock_data.get_fmp_client", return_value=mock_fmp_client),
        patch("app.services.stock_data.yf_client", mock_yf_client),
    ):
        results = await search_stocks_from_yfinance("HIMS")

    symbols = [r.symbol for r in results]
    assert "HIMS" in symbols
