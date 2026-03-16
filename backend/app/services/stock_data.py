"""YFinance data fetching: price, history, info, news, search."""

import asyncio
import time
from typing import Any, Optional, cast

import yfinance as yf
from fastapi import HTTPException, status

from app.core.cache import cache_get, cache_set
from app.core.executors import get_executor
from app.schemas.stock import (
    StockDataResponse,
    StockHistoryPoint,
    StockHistoryResponse,
    StockInfoResponse,
    StockNewsItem,
    StockSearchResult,
)

_CACHE_TTL = 300  # 5 minutes - reduce Yahoo rate limit hits
_INFO_CACHE_TTL = 600  # 10 minutes
_SEARCH_CACHE_TTL = 120  # 2 minutes - search results
_HISTORY_CACHE_TTL = 300  # 5 minutes - historical charts

# Fallback in-memory for search results (not serializable to JSON easily)
_stock_data_cache: dict[str, tuple[StockDataResponse, float]] = {}

# Exchange code → display name
_EXCHANGE_DISPLAY: dict[str, str] = {
    "NMS": "NASDAQ",
    "NGM": "NASDAQ",
    "NYS": "NYSE",
    "NYQ": "NYSE",
    "ASE": "NYSE American",
    "PCX": "NYSE Arca",
}

# Exchange code → country mapping
_EXCHANGE_COUNTRY: dict[str, str] = {
    "NMS": "United States",
    "NGS": "United States",
    "NYQ": "United States",
    "ASE": "United States",
    "PCX": "United States",
    "OTC": "United States",
    "FRA": "Germany",
    "LSE": "United Kingdom",
    "TSX": "Canada",
    "TYO": "Japan",
    "HKG": "Hong Kong",
    "SHH": "China",
    "SHZ": "China",
    "ASX": "Australia",
}


def _fetch_price_sync(symbol: str) -> Optional[float]:
    """Fetch last price synchronously (runs in executor thread)."""
    try:
        fast_info = yf.Ticker(symbol).fast_info
        price = fast_info.last_price
        return round(float(price), 2) if price else None
    except Exception:
        return None


def _fetch_sparkline_sync(symbol: str) -> Optional[list[float]]:
    """Fetch last 5 daily closing prices for a sparkline (runs in executor thread)."""
    try:
        hist = yf.Ticker(symbol).history(period="5d", interval="1d")
        if hist.empty:
            return None
        closes = hist["Close"].dropna().tolist()
        return [round(float(p), 2) for p in closes] if closes else None
    except Exception:
        return None


def _lookup_ticker_direct_sync(symbol: str) -> Optional[dict]:
    """Fallback: direct Ticker lookup when Search returns empty. Returns dict compatible with equities item."""
    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info
        if not info or not info.get("symbol"):
            return None
        quote_type = info.get("quoteType", "")
        if quote_type and quote_type not in ("EQUITY", "ETF"):
            return None
        fast_info = ticker.fast_info
        price = fast_info.last_price if fast_info else None
        hist = ticker.history(period="5d", interval="1d")
        sparkline = None
        if not hist.empty and "Close" in hist.columns:
            closes = hist["Close"].dropna().tolist()
            sparkline = [round(float(p), 2) for p in closes] if closes else None
        exch_code = info.get("exchange", "")
        exch_disp = _EXCHANGE_DISPLAY.get(exch_code, exch_code) if exch_code else ""
        currency = str(fast_info.currency) if fast_info and fast_info.currency else None
        return {
            "symbol": info.get("symbol", symbol),
            "longname": info.get("longName") or info.get("shortName"),
            "shortname": info.get("shortName") or info.get("longName"),
            "exchange": exch_code,
            "exchDisp": exch_disp or exch_code,
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "quoteType": quote_type or "EQUITY",
            "_price": round(float(price), 2) if price else None,
            "_sparkline": sparkline,
            "_currency": currency,
        }
    except Exception:
        return None


def _fetch_stock_data_sync(symbol: str) -> Optional[StockDataResponse]:
    """Fetch stock data synchronously (runs in executor). Returns None on failure."""
    def _safe_int(x: Any) -> Optional[int]:
        if x is None or (isinstance(x, float) and x != x):
            return None
        try:
            return int(x)
        except (ValueError, TypeError, OverflowError):
            return None

    def _from_history(ticker: Any) -> Optional[StockDataResponse]:
        """Fallback when fast_info fails (KeyError, etc.)."""
        try:
            hist = ticker.history(period="5d", interval="1d")
            if hist.empty or "Close" not in hist.columns:
                return None
            closes = hist["Close"].dropna()
            if len(closes) < 1:
                return None
            current_price = float(closes.iloc[-1])
            previous_close = float(closes.iloc[-2]) if len(closes) >= 2 else current_price
            if current_price <= 0:
                return None
            change = current_price - previous_close
            change_percent = (change / previous_close * 100) if previous_close > 0 else 0.0
            return StockDataResponse(
                symbol=symbol,
                name=symbol,
                current_price=round(current_price, 2),
                previous_close=round(previous_close, 2),
                change=round(change, 2),
                change_percent=round(change_percent, 2),
                volume=None,
                market_cap=None,
                currency="USD",
            )
        except Exception as e:
            if "429" in str(e) or "Too Many Requests" in str(e):
                raise
            return None

    try:
        ticker = yf.Ticker(symbol)
        fast_info = ticker.fast_info
        if fast_info is None:
            return _from_history(ticker)

        try:
            last_price = getattr(fast_info, "last_price", None)
            previous_close = getattr(fast_info, "previous_close", None) or last_price
        except (KeyError, Exception):
            return _from_history(ticker)

        current_price = float(last_price or 0)
        previous_close = float(previous_close or current_price)

        if current_price == 0:
            return _from_history(ticker)

        change = current_price - previous_close
        change_percent = (change / previous_close * 100) if previous_close > 0 else 0.0

        vol = getattr(fast_info, "three_month_average_volume", None)
        mcap = getattr(fast_info, "market_cap", None)
        currency_val = getattr(fast_info, "currency", None)

        volume = _safe_int(vol)
        market_cap = _safe_int(mcap)
        currency = str(currency_val) if currency_val else "USD"

        return StockDataResponse(
            symbol=symbol,
            name=symbol,
            current_price=round(current_price, 2),
            previous_close=round(previous_close, 2),
            change=round(change, 2),
            change_percent=round(change_percent, 2),
            volume=volume,
            market_cap=market_cap,
            currency=currency,
        )
    except Exception as e:
        if "429" in str(e) or "Too Many Requests" in str(e):
            raise
        return None


async def fetch_stock_data_from_yfinance(symbol: str) -> StockDataResponse:
    """Fetch live stock data from yfinance API using fast_info to avoid rate limits."""
    sym = symbol.upper()
    cache_key = f"stock_data:{sym}"

    cached = await cache_get(cache_key)
    if cached:
        return StockDataResponse.model_validate(cached)

    if sym in _stock_data_cache:
        cached_data, cached_at = _stock_data_cache[sym]
        if time.time() - cached_at < _CACHE_TTL:
            return cached_data

    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(get_executor(), _fetch_stock_data_sync, sym)

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Stock data not found for symbol {symbol}",
            )

        _stock_data_cache[sym] = (result, time.time())
        await cache_set(cache_key, result.model_dump(mode="json"), ttl=_CACHE_TTL)
        return result

    except HTTPException:
        raise
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "Too Many Requests" in error_str:
            if sym in _stock_data_cache:
                return _stock_data_cache[sym][0]
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Yahoo Finance rate limit. Please try again in 5-10 minutes.",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching stock data: {error_str}",
        ) from e


async def fetch_stock_data_batch(symbols: list[str]) -> dict[str, StockDataResponse]:
    """Fetch stock data for multiple symbols in parallel. Returns dict symbol -> data; skips failures."""
    if not symbols:
        return {}
    syms = list(dict.fromkeys(s.upper() for s in symbols))[:50]  # dedupe, max 50
    results = await asyncio.gather(
        *[fetch_stock_data_from_yfinance(s) for s in syms],
        return_exceptions=True,
    )
    out: dict[str, StockDataResponse] = {}
    for sym, r in zip(syms, results):
        if isinstance(r, StockDataResponse):
            out[sym] = r
    return out


async def search_stocks_from_yfinance(query: str, limit: int = 8) -> list[StockSearchResult]:
    """Search for stocks by ticker or company name using yfinance."""
    cache_key = f"stock_search:{query.lower()}:{limit}"
    cached = await cache_get(cache_key)
    if cached:
        return [StockSearchResult.model_validate(r) for r in cached]

    loop = asyncio.get_running_loop()
    q_upper = query.strip().upper()

    def _do_search() -> list[dict]:
        try:
            results = yf.Search(q_upper, max_results=20).quotes
            return results if isinstance(results, list) else []
        except Exception:
            return []

    raw_results = await loop.run_in_executor(get_executor(), _do_search)

    equities = [
        r for r in raw_results
        if r.get("quoteType") in ("EQUITY", "ETF", None)
    ][:limit]

    if not equities and 1 <= len(q_upper) <= 10 and q_upper.replace(".", "").isalnum():
        direct = await loop.run_in_executor(
            get_executor(),
            _lookup_ticker_direct_sync,
            q_upper,
        )
        if direct:
            equities = [direct]

    price_tasks = [
        loop.run_in_executor(get_executor(), _fetch_price_sync, r["symbol"])
        for r in equities
    ]
    sparkline_tasks = [
        loop.run_in_executor(get_executor(), _fetch_sparkline_sync, r["symbol"])
        for r in equities
    ]
    gathered = await asyncio.gather(*price_tasks, *sparkline_tasks)
    prices = gathered[: len(equities)]
    sparklines = gathered[len(equities) :]

    results: list[StockSearchResult] = []
    for item, price, sparkline in zip(equities, prices, sparklines):
        symbol = item.get("symbol", "")
        exch_code = item.get("exchange", "")
        exch_display = item.get("exchDisp", exch_code)
        country = _EXCHANGE_COUNTRY.get(exch_code)

        currency: Optional[str] = item.get("_currency")
        if currency is None and symbol in _stock_data_cache:
            currency = _stock_data_cache[symbol][0].currency

        use_price = item.get("_price") if "_price" in item else price
        use_sparkline = item.get("_sparkline") if "_sparkline" in item else sparkline

        results.append(
            StockSearchResult(
                symbol=symbol,
                name=item.get("longname") or item.get("shortname") or symbol,
                exchange=exch_display,
                sector=item.get("sector"),
                industry=item.get("industry"),
                current_price=cast(Optional[float], use_price),
                currency=currency,
                country=country,
                sparkline=cast(Optional[list[float]], use_sparkline),
            )
        )

    serializable = [r.model_dump(mode="json") for r in results]
    await cache_set(cache_key, serializable, ttl=_SEARCH_CACHE_TTL)
    return results


_PERIOD_MAP: dict[str, tuple[str, str]] = {
    "1d": ("1d", "5m"),
    "1w": ("5d", "30m"),
    "1m": ("1mo", "1d"),
    "6m": ("6mo", "1d"),
    "1y": ("1y", "1d"),
}


async def fetch_stock_history(symbol: str, period: str = "1m") -> StockHistoryResponse:
    """Fetch OHLCV price history for a stock symbol."""
    sym = symbol.upper()
    cache_key = f"stock_history:{sym}:{period}"
    cached = await cache_get(cache_key)
    if cached:
        return StockHistoryResponse.model_validate(cached)

    yf_period, yf_interval = _PERIOD_MAP.get(period, ("1mo", "1d"))
    loop = asyncio.get_running_loop()

    def _fetch() -> list[StockHistoryPoint]:
        hist = yf.Ticker(sym).history(period=yf_period, interval=yf_interval)
        if hist.empty:
            return []
        points: list[StockHistoryPoint] = []
        for ts, row in hist.iterrows():
            t_ms = int(ts.timestamp() * 1000)
            vol = row.get("Volume")
            v_int: Optional[int] = None
            if vol is not None and vol == vol:
                v_int = int(vol)
            points.append(
                StockHistoryPoint(
                    t=t_ms,
                    o=round(float(row["Open"]), 4),
                    h=round(float(row["High"]), 4),
                    l=round(float(row["Low"]), 4),
                    c=round(float(row["Close"]), 4),
                    v=v_int,
                )
            )
        return points

    try:
        data = await loop.run_in_executor(get_executor(), _fetch)
        result = StockHistoryResponse(symbol=sym, period=period, data=data)
        await cache_set(cache_key, result.model_dump(mode="json"), ttl=_HISTORY_CACHE_TTL)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching history for {symbol}: {e}",
        ) from e


def _safe_info_val(val: Any) -> Any:
    """Convert yfinance values to JSON-safe types (avoids datetime/str type errors)."""
    if val is None:
        return None
    if hasattr(val, "isoformat"):  # datetime, date, Timestamp - skip, often cause type errors
        return None
    if isinstance(val, (int, float)) and val != val:  # NaN
        return None
    return val


def _fetch_stock_info_sync(symbol: str) -> StockInfoResponse:
    """Fetch stock info synchronously (runs in executor). Handles yfinance datetime/str bugs."""
    sym = symbol.upper()
    try:
        ticker = yf.Ticker(sym)
        raw = ticker.info
        if not raw:
            return StockInfoResponse(symbol=sym)
    except TypeError as e:
        if "datetime" in str(e) and "str" in str(e):
            # yfinance bug: unsupported operand type(s) for -: 'datetime.datetime' and 'str'
            return StockInfoResponse(symbol=sym)
        raise
    except Exception as e:
        if "429" in str(e) or "Too Many Requests" in str(e):
            return StockInfoResponse(symbol=sym)
        raise

    # Extract only needed keys; sanitize values to avoid type errors
    def get(k: str) -> Any:
        v = raw.get(k)
        return _safe_info_val(v) if v is not None else None

    ceo: Optional[str] = None
    officers = raw.get("companyOfficers") or []
    for officer in officers:
        if not isinstance(officer, dict):
            continue
        title = (officer.get("title") or "").lower()
        if "ceo" in title or "chief executive" in title:
            ceo = officer.get("name")
            break

    def safe_int(x: Any) -> Optional[int]:
        if x is None or (isinstance(x, float) and x != x):
            return None
        try:
            return int(x)
        except (ValueError, TypeError, OverflowError):
            return None

    def safe_float(x: Any) -> Optional[float]:
        if x is None or (isinstance(x, float) and x != x):
            return None
        try:
            return float(x)
        except (ValueError, TypeError, OverflowError):
            return None

    return StockInfoResponse(
        symbol=sym,
        description=get("longBusinessSummary"),
        website=get("website"),
        employees=safe_int(get("fullTimeEmployees")),
        ceo=ceo,
        country=get("country"),
        sector=get("sector"),
        industry=get("industry"),
        market_cap=safe_float(get("marketCap")),
        pe_ratio=safe_float(get("trailingPE")),
        forward_pe=safe_float(get("forwardPE")),
        beta=safe_float(get("beta")),
        dividend_yield=safe_float(get("dividendYield")),
        fifty_two_week_high=safe_float(get("fiftyTwoWeekHigh")),
        fifty_two_week_low=safe_float(get("fiftyTwoWeekLow")),
        average_volume=safe_int(get("averageVolume")),
    )


async def fetch_stock_info(symbol: str) -> StockInfoResponse:
    """Fetch detailed company info for a stock (10-min cache)."""
    sym = symbol.upper()
    cache_key = f"stock_info:{sym}"

    cached = await cache_get(cache_key)
    if cached:
        return StockInfoResponse.model_validate(cached)

    loop = asyncio.get_running_loop()

    try:
        result = await loop.run_in_executor(
            get_executor(), _fetch_stock_info_sync, sym
        )
        await cache_set(cache_key, result.model_dump(mode="json"), ttl=_INFO_CACHE_TTL)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching info for {symbol}: {e}",
        ) from e


_NEWS_CACHE_TTL = 300  # 5 minutes


async def fetch_stock_news(symbol: str, limit: int = 8) -> list[StockNewsItem]:
    """Fetch recent news articles for a stock. Returns empty list on Yahoo API failure."""
    sym = symbol.upper()
    cache_key = f"stock_news:{sym}:{limit}"
    cached = await cache_get(cache_key)
    if cached:
        return [StockNewsItem.model_validate(r) for r in cached]

    loop = asyncio.get_running_loop()

    def _fetch() -> list[dict]:
        try:
            news = yf.Ticker(sym).news
            return news if isinstance(news, list) else []
        except Exception:
            return []

    try:
        raw_news = await loop.run_in_executor(get_executor(), _fetch)
        items: list[StockNewsItem] = []
        for article in raw_news[:limit]:
            content = article.get("content") or article

            title = content.get("title", "") or article.get("title", "")

            publisher: Optional[str] = None
            provider = content.get("provider")
            if isinstance(provider, dict):
                publisher = provider.get("displayName")
            elif isinstance(provider, str):
                publisher = provider
            else:
                publisher = article.get("publisher")

            link: Optional[str] = None
            canonical = content.get("canonicalUrl") or content.get("clickThroughUrl")
            if isinstance(canonical, dict):
                link = canonical.get("url")
            if not link:
                link = article.get("link")

            published_at: Optional[int] = None
            pub_date = content.get("pubDate") or content.get("displayTime")
            if pub_date:
                from datetime import datetime

                try:
                    dt = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                    published_at = int(dt.timestamp() * 1000)
                except Exception:
                    pass
            if not published_at:
                pt = article.get("providerPublishTime")
                if pt:
                    published_at = int(pt) * 1000

            items.append(
                StockNewsItem(
                    title=title,
                    publisher=publisher,
                    link=link,
                    published_at=published_at,
                )
            )
        if items:
            await cache_set(cache_key, [i.model_dump(mode="json") for i in items], ttl=_NEWS_CACHE_TTL)
        return items
    except Exception:
        # Yahoo news API can fail (rate limit, invalid JSON, etc.) - return empty
        return []
