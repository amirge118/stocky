"""FMP data fetching: price, history, info, news, search, dividends."""

import asyncio
from datetime import date, datetime, timedelta
from typing import Any, Optional, cast

from fastapi import HTTPException, status

from app.core.cache import cache_get, cache_set
from app.core.fmp_client import FMPNotFoundError, FMPRateLimitError, get_fmp_client
from app.schemas.stock import (
    DividendPoint,
    StockDataResponse,
    StockDividendsResponse,
    StockHistoryPoint,
    StockHistoryResponse,
    StockInfoResponse,
    StockNewsItem,
    StockSearchResult,
)

_CACHE_TTL = 600          # 10 minutes
_INFO_CACHE_TTL = 1800    # 30 minutes
_SEARCH_CACHE_TTL = 600   # 10 minutes
_HISTORY_CACHE_TTL = 900  # 15 minutes
_NEWS_CACHE_TTL = 900     # 15 minutes
_DIVIDENDS_CACHE_TTL = 7200  # 2 hours


def _safe_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    try:
        v = float(x)
        return None if v != v else v  # NaN → None
    except (ValueError, TypeError):
        return None


def _safe_int(x: Any) -> Optional[int]:
    if x is None:
        return None
    try:
        v = float(x)
        if v != v:
            return None
        return int(v)
    except (ValueError, TypeError, OverflowError):
        return None


async def search_stocks_from_yfinance(query: str, limit: int = 8) -> list[StockSearchResult]:
    """Search for stocks by ticker or company name using FMP."""
    cache_key = f"stock_search:{query.lower()}:{limit}"
    cached = await cache_get(cache_key)
    if cached:
        return [StockSearchResult.model_validate(r) for r in cached]

    client = get_fmp_client()
    try:
        raw = await client.get("/stable/search-symbol", {"query": query.strip(), "limit": 20})
    except FMPRateLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Data provider rate limit. Please try again shortly.",
        ) from e
    except Exception:
        raw = []

    items = (raw if isinstance(raw, list) else [])[:limit]
    if not items:
        return []

    # Enrich with live quotes (individual concurrent requests)
    symbols = [item["symbol"] for item in items if item.get("symbol")]
    quote_results = await asyncio.gather(*[_fetch_single_quote(client, s) for s in symbols])
    quotes = {s: q for s, q in zip(symbols, quote_results) if q}

    results: list[StockSearchResult] = []
    for item in items:
        sym = item.get("symbol", "")
        q = quotes.get(sym, {})
        results.append(
            StockSearchResult(
                symbol=sym,
                name=item.get("name") or sym,
                exchange=item.get("stockExchange") or item.get("exchangeShortName") or "",
                sector=None,
                industry=None,
                current_price=_safe_float(q.get("price")),
                currency=item.get("currency"),
                country=None,
                sparkline=None,
            )
        )

    serializable = [r.model_dump(mode="json") for r in results]
    await cache_set(cache_key, serializable, ttl=_SEARCH_CACHE_TTL)
    return results


async def fetch_stock_data_from_yfinance(symbol: str) -> StockDataResponse:
    """Fetch live stock data from FMP API."""
    sym = symbol.upper()
    cache_key = f"stock_data:{sym}"

    cached = await cache_get(cache_key)
    if cached:
        return StockDataResponse.model_validate(cached)

    client = get_fmp_client()
    try:
        raw = await client.get("/stable/quote", {"symbol": sym})
    except FMPRateLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Data provider rate limit. Please try again shortly.",
        ) from e
    except FMPNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock data not found for symbol {symbol}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching stock data: {e}",
        ) from e

    quotes = raw if isinstance(raw, list) else []
    if not quotes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock data not found for symbol {symbol}",
        )

    q = quotes[0]
    price = _safe_float(q.get("price")) or 0.0
    prev_close = _safe_float(q.get("previousClose")) or price
    change = _safe_float(q.get("change")) or (price - prev_close)
    change_pct = _safe_float(q.get("changePercentage")) or (
        (change / prev_close * 100) if prev_close > 0 else 0.0
    )

    result = StockDataResponse(
        symbol=sym,
        name=q.get("name") or sym,
        current_price=round(price, 2),
        previous_close=round(prev_close, 2),
        change=round(change, 2),
        change_percent=round(change_pct, 2),
        volume=_safe_int(q.get("volume")),
        market_cap=_safe_float(q.get("marketCap")),
        currency="USD",
    )

    await cache_set(cache_key, result.model_dump(mode="json"), ttl=_CACHE_TTL)
    return result


async def _fetch_single_quote(client: object, sym: str) -> Optional[dict]:
    """Fetch a single quote dict from FMP, returning None on failure."""
    try:
        raw = await client.get("/stable/quote", {"symbol": sym})  # type: ignore[union-attr]
        items = raw if isinstance(raw, list) else []
        return items[0] if items else None
    except Exception:
        return None


async def fetch_stock_data_batch(symbols: list[str]) -> dict[str, StockDataResponse]:
    """Fetch stock data for multiple symbols via concurrent individual FMP calls."""
    if not symbols:
        return {}
    syms = list(dict.fromkeys(s.upper() for s in symbols))[:50]

    client = get_fmp_client()
    results = await asyncio.gather(*[_fetch_single_quote(client, sym) for sym in syms])

    out: dict[str, StockDataResponse] = {}
    for sym, q in zip(syms, results):
        if not q:
            continue
        price = _safe_float(q.get("price")) or 0.0
        if price == 0:
            continue
        prev_close = _safe_float(q.get("previousClose")) or price
        change = _safe_float(q.get("change")) or (price - prev_close)
        change_pct = _safe_float(q.get("changePercentage")) or 0.0
        out[sym] = StockDataResponse(
            symbol=sym,
            name=q.get("name") or sym,
            current_price=round(price, 2),
            previous_close=round(prev_close, 2),
            change=round(change, 2),
            change_percent=round(change_pct, 2),
            volume=_safe_int(q.get("volume")),
            market_cap=_safe_float(q.get("marketCap")),
            currency="USD",
        )
    return out


def _date_range(period: str) -> tuple[str, str]:
    """Return (from_date, to_date) ISO strings for a given period."""
    today = date.today()
    period_days: dict[str, int] = {
        "1d": 1,
        "1w": 7,
        "1m": 31,
        "6m": 183,
        "1y": 365,
        "2y": 730,
        "5y": 1825,
    }
    days = period_days.get(period, 31)
    return (today - timedelta(days=days)).isoformat(), today.isoformat()


async def fetch_stock_history(symbol: str, period: str = "1m") -> StockHistoryResponse:
    """Fetch OHLCV price history from FMP."""
    sym = symbol.upper()
    cache_key = f"stock_history:{sym}:{period}"
    cached = await cache_get(cache_key)
    if cached:
        return StockHistoryResponse.model_validate(cached)

    client = get_fmp_client()
    from_date, to_date = _date_range(period)

    try:
        if period == "1d":
            raw = await client.get(
                "/stable/intraday/5-min", {"symbol": sym, "from": from_date, "to": to_date}
            )
            items = raw if isinstance(raw, list) else []
        elif period == "1w":
            raw = await client.get(
                "/stable/intraday/15-min", {"symbol": sym, "from": from_date, "to": to_date}
            )
            items = raw if isinstance(raw, list) else []
        else:
            raw = await client.get(
                "/stable/historical-price-eod/full", {"symbol": sym, "from": from_date, "to": to_date}
            )
            items = raw if isinstance(raw, list) else (raw if isinstance(raw, dict) else {}).get("historical", [])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching history for {symbol}: {e}",
        ) from e

    # FMP returns newest-first; reverse to chronological order
    items = list(reversed(items))

    points: list[StockHistoryPoint] = []
    for item in items:
        date_str = item.get("date", "")
        if not date_str:
            continue
        try:
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
            t_ms = int(dt.timestamp() * 1000)
        except Exception:
            continue
        points.append(
            StockHistoryPoint(
                t=t_ms,
                o=round(float(item.get("open", 0)), 4),
                h=round(float(item.get("high", 0)), 4),
                l=round(float(item.get("low", 0)), 4),
                c=round(float(item.get("close", 0)), 4),
                v=_safe_int(item.get("volume")),
            )
        )

    result = StockHistoryResponse(symbol=sym, period=period, data=points)
    await cache_set(cache_key, result.model_dump(mode="json"), ttl=_HISTORY_CACHE_TTL)
    return result


async def fetch_stock_info(symbol: str) -> StockInfoResponse:
    """Fetch detailed company info from FMP (profile + quote, concurrent)."""
    sym = symbol.upper()
    cache_key = f"stock_info:{sym}"

    cached = await cache_get(cache_key)
    if cached:
        return StockInfoResponse.model_validate(cached)

    client = get_fmp_client()
    try:
        profile_raw, quote_raw = await asyncio.gather(
            client.get("/stable/profile", {"symbol": sym}),
            client.get("/stable/quote", {"symbol": sym}),
            return_exceptions=True,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching info for {symbol}: {e}",
        ) from e

    p: dict = profile_raw[0] if isinstance(profile_raw, list) and profile_raw else {}
    q: dict = quote_raw[0] if isinstance(quote_raw, list) and quote_raw else {}

    employees_raw = p.get("fullTimeEmployees")
    employees: Optional[int] = None
    if employees_raw is not None:
        try:
            employees = int(str(employees_raw).replace(",", ""))
        except (ValueError, TypeError):
            pass

    market_cap = _safe_float(p.get("mktCap")) or _safe_float(q.get("marketCap"))
    price = _safe_float(q.get("price")) or _safe_float(p.get("price"))
    last_div = _safe_float(p.get("lastDiv"))
    dividend_yield: Optional[float] = None
    if last_div and price and price > 0:
        dividend_yield = round(last_div / price * 100, 4)

    result = StockInfoResponse(
        symbol=sym,
        description=p.get("description"),
        website=p.get("website"),
        employees=employees,
        ceo=p.get("ceo"),
        country=p.get("country"),
        sector=p.get("sector"),
        industry=p.get("industry"),
        market_cap=market_cap,
        pe_ratio=_safe_float(q.get("pe")),
        forward_pe=None,  # requires key-metrics endpoint (higher tier)
        beta=_safe_float(p.get("beta")),
        dividend_yield=dividend_yield,
        fifty_two_week_high=_safe_float(q.get("yearHigh")),
        fifty_two_week_low=_safe_float(q.get("yearLow")),
        average_volume=_safe_int(q.get("avgVolume")),
    )

    await cache_set(cache_key, result.model_dump(mode="json"), ttl=_INFO_CACHE_TTL)
    return result


async def fetch_stock_news(symbol: str, limit: int = 8) -> list[StockNewsItem]:
    """Fetch recent news from FMP. Returns empty list on failure."""
    sym = symbol.upper()
    cache_key = f"stock_news:{sym}:{limit}"
    cached = await cache_get(cache_key)
    if cached:
        return [StockNewsItem.model_validate(r) for r in cached]

    client = get_fmp_client()
    try:
        raw = await client.get("/stable/stock-news", {"symbol": sym, "limit": limit})
    except Exception:
        return []

    items: list[StockNewsItem] = []
    for article in (raw if isinstance(raw, list) else []):
        title = article.get("title", "")
        if not title:
            continue
        published_at: Optional[int] = None
        pub_date = article.get("publishedDate")
        if pub_date:
            try:
                dt = datetime.strptime(pub_date[:19], "%Y-%m-%d %H:%M:%S")
                published_at = int(dt.timestamp() * 1000)
            except Exception:
                pass
        items.append(
            StockNewsItem(
                title=title,
                publisher=article.get("site"),
                link=article.get("url"),
                published_at=published_at,
            )
        )

    if items:
        await cache_set(
            cache_key, [i.model_dump(mode="json") for i in items], ttl=_NEWS_CACHE_TTL
        )
    return items


async def fetch_stock_dividends(symbol: str, years: int = 5) -> StockDividendsResponse:
    """Fetch dividend history from FMP (last N years)."""
    sym = symbol.upper()
    cache_key = f"stock_dividends:{sym}:{years}"
    cached = await cache_get(cache_key)
    if cached:
        return StockDividendsResponse.model_validate(cached)

    client = get_fmp_client()
    try:
        raw, quote_raw = await asyncio.gather(
            client.get("/stable/dividends", {"symbol": sym}),
            client.get("/stable/quote", {"symbol": sym}),
            return_exceptions=True,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching dividends for {symbol}: {e}",
        ) from e

    historical: list[dict] = []
    if isinstance(raw, list):
        historical = raw
    elif isinstance(raw, dict):
        historical = raw.get("historical", [])

    cutoff = date.today() - timedelta(days=years * 365)
    one_year_ago = date.today() - timedelta(days=365)
    points: list[DividendPoint] = []
    trailing_sum = 0.0

    for div in historical:
        div_date_str = div.get("date", "")
        if not div_date_str:
            continue
        try:
            div_date = date.fromisoformat(div_date_str[:10])
        except ValueError:
            continue
        if div_date < cutoff:
            continue
        amount = _safe_float(div.get("dividend") or div.get("adjDividend"))
        if amount is None:
            continue
        t_ms = int(
            datetime.combine(div_date, datetime.min.time()).timestamp() * 1000
        )
        points.append(DividendPoint(t=t_ms, amount=round(amount, 4)))
        if div_date >= one_year_ago:
            trailing_sum += amount

    # FMP returns newest-first; reverse to chronological
    points = list(reversed(points))

    annual_yield: Optional[float] = None
    price: Optional[float] = None
    if isinstance(quote_raw, list) and quote_raw:
        price = _safe_float(quote_raw[0].get("price"))
    if price and price > 0 and trailing_sum > 0:
        annual_yield = round(trailing_sum / price * 100, 2)

    result = StockDividendsResponse(
        symbol=sym,
        currency="USD",
        dividends=points,
        annual_yield=annual_yield,
    )
    await cache_set(cache_key, result.model_dump(mode="json"), ttl=_DIVIDENDS_CACHE_TTL)
    return result
