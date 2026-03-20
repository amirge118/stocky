"""Stock data fetching: FMP primary, yfinance fallback/TASE.

Routing rules:
- Symbols ending in .TA (TASE) → yfinance only
- All others → FMP first, yfinance fallback on empty/zero data
- FMPRateLimitError always falls back to yfinance; never surfaces as HTTP 503
"""

import asyncio
import logging
from datetime import date, datetime, timedelta
from typing import Any, Optional

from fastapi import HTTPException, status

from app.core import yf_client
from app.core.cache import cache_get, cache_set
from app.core.fmp_client import FMPNotFoundError, FMPRateLimitError, get_fmp_client
from app.schemas.stock import (
    DividendPoint,
    StockDataResponse,
    StockDividendsResponse,
    StockEnrichedData,
    StockHistoryPoint,
    StockHistoryResponse,
    StockInfoResponse,
    StockNewsItem,
    StockSearchResult,
)

logger = logging.getLogger(__name__)

_CACHE_TTL = 600          # 10 minutes
_INFO_CACHE_TTL = 1800    # 30 minutes
_SEARCH_CACHE_TTL = 600   # 10 minutes
_HISTORY_CACHE_TTL = 900  # 15 minutes
_NEWS_CACHE_TTL = 900     # 15 minutes
_DIVIDENDS_CACHE_TTL = 7200  # 2 hours
_QUOTE_CACHE_TTL = 300    # 5 min — shared across all services
_ENRICHED_CACHE_TTL = 3600  # 1 hour — 52W range, avg volume, analyst rating


def _is_tase(symbol: str) -> bool:
    return symbol.upper().endswith(".TA")


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


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _yf_history_to_response(sym: str, period: str, rows: list[dict]) -> StockHistoryResponse:
    """Convert yfinance history row dicts to StockHistoryResponse."""
    points: list[StockHistoryPoint] = []
    for item in rows:
        date_str = item.get("date", "")
        if not date_str:
            continue
        try:
            dt = datetime.fromisoformat(date_str)
            t_ms = int(dt.timestamp() * 1000)
        except Exception:
            continue
        points.append(StockHistoryPoint(
            t=t_ms,
            o=round(float(item.get("open", 0)), 4),
            h=round(float(item.get("high", 0)), 4),
            l=round(float(item.get("low", 0)), 4),
            c=round(float(item.get("close", 0)), 4),
            v=_safe_int(item.get("volume")),
        ))
    return StockHistoryResponse(symbol=sym, period=period, data=points)


def _yf_quote_to_response(sym: str, q: dict) -> StockDataResponse:
    """Build StockDataResponse from a yfinance-style quote dict."""
    price = _safe_float(q.get("price")) or 0.0
    change = _safe_float(q.get("change")) or 0.0
    prev_close = _safe_float(q.get("previousClose")) or (price - change) or price
    change_pct = _safe_float(q.get("changePercentage")) or (
        (change / prev_close * 100) if prev_close > 0 else 0.0
    )
    return StockDataResponse(
        symbol=sym,
        name=q.get("companyName") or sym,
        current_price=round(price, 2),
        previous_close=round(prev_close, 2),
        change=round(change, 2),
        change_percent=round(change_pct, 2),
        volume=_safe_int(q.get("volume")),
        market_cap=_safe_float(q.get("marketCap")),
        currency=q.get("currency") or "USD",
    )


async def _fetch_single_quote(client: object, sym: str) -> Optional[dict]:
    """Fetch a single quote dict from FMP profile endpoint, yfinance fallback on failure."""
    try:
        raw = await client.get("/stable/profile", {"symbol": sym})  # type: ignore[union-attr]
        items = raw if isinstance(raw, list) else []
        if items:
            return items[0]
    except Exception:
        pass
    # FMP unavailable / rate-limited → yfinance fallback
    return await yf_client.fetch_quote(sym)


async def _get_cached_quote(client: object, sym: str) -> Optional[dict]:
    """Fetch a single quote dict, shared across all services via quote:{sym} cache key."""
    cached = await cache_get(f"quote:{sym}")
    if cached is not None:
        return cached
    q = await _fetch_single_quote(client, sym)
    if q is not None:
        await cache_set(f"quote:{sym}", q, ttl=_QUOTE_CACHE_TTL)
    return q


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

async def search_stocks_from_yfinance(query: str, limit: int = 8) -> list[StockSearchResult]:
    """Search for stocks using FMP + yfinance Search + TASE table.

    Merge order: TASE matches first (always visible), then yfinance Search,
    then FMP — so TASE symbols are never crowded out.
    """
    cache_key = f"stock_search:{query.lower()}:{limit}"
    cached = await cache_get(cache_key)
    if cached:
        return [StockSearchResult.model_validate(r) for r in cached]

    client = get_fmp_client()

    async def _fmp_search() -> list[dict]:
        try:
            raw = await client.get("/stable/search-symbol", {"query": query.strip(), "limit": 20})
            return raw if isinstance(raw, list) else []
        except FMPRateLimitError:
            logger.warning("FMP rate limit hit during search for %r — falling back to yfinance only", query)
            return []
        except Exception:
            return []

    # Run FMP + yfinance Search concurrently; TASE table lookup is instant
    tase_raw = yf_client.search_tase(query, limit)
    fmp_items, yf_items = await asyncio.gather(
        _fmp_search(),
        yf_client.search_yf(query, limit),
    )

    tase_items = [
        {
            "symbol": t["symbol"],
            "name": t["name"],
            "stockExchange": t["exchange"],
            "exchangeShortName": t["exchange"],
            "currency": "ILS",
            "country": t.get("country"),
        }
        for t in tase_raw
    ]

    # Filter yf results: skip TASE (already covered) and empty symbols
    yf_filtered = [
        i for i in yf_items
        if i.get("symbol") and not _is_tase(i["symbol"])
    ]

    # Merge: TASE first so they're never cut off, then yfinance, then FMP
    seen: set[str] = set()
    merged: list[dict] = []
    for item in tase_items + yf_filtered + fmp_items:
        sym = item.get("symbol", "")
        if sym and sym not in seen:
            seen.add(sym)
            merged.append(item)

    items = merged[:limit]
    if not items:
        return []

    # Enrich with live quotes: FMP for non-TASE, yfinance for TASE
    fmp_symbols = [i["symbol"] for i in items if i.get("symbol") and not _is_tase(i["symbol"])]
    tase_symbols = [i["symbol"] for i in items if i.get("symbol") and _is_tase(i["symbol"])]

    fmp_quotes_raw, tase_quotes_raw = await asyncio.gather(
        asyncio.gather(*[_fetch_single_quote(client, s) for s in fmp_symbols]),
        asyncio.gather(*[yf_client.fetch_quote(s) for s in tase_symbols]),
    )

    quotes: dict[str, dict] = {}
    for s, q in zip(fmp_symbols, fmp_quotes_raw):
        if q:
            quotes[s] = q
    for s, q in zip(tase_symbols, tase_quotes_raw):
        if q:
            quotes[s] = q

    results: list[StockSearchResult] = []
    for item in items:
        sym = item.get("symbol", "")
        q = quotes.get(sym, {})
        results.append(StockSearchResult(
            symbol=sym,
            name=item.get("name") or sym,
            exchange=item.get("stockExchange") or item.get("exchangeShortName") or "",
            sector=None,
            industry=None,
            current_price=_safe_float(q.get("price")),
            currency=item.get("currency") or q.get("currency"),
            country=item.get("country"),
            sparkline=None,
        ))

    serializable = [r.model_dump(mode="json") for r in results]
    await cache_set(cache_key, serializable, ttl=_SEARCH_CACHE_TTL)
    return results


# ---------------------------------------------------------------------------
# Live quote
# ---------------------------------------------------------------------------

async def fetch_stock_data_from_yfinance(symbol: str) -> StockDataResponse:
    """Fetch live stock data. TASE → yfinance; others → FMP with yfinance fallback."""
    sym = symbol.upper()
    cache_key = f"stock_data:{sym}"

    cached = await cache_get(cache_key)
    if cached:
        return StockDataResponse.model_validate(cached)

    # TASE: go directly to yfinance
    if _is_tase(sym):
        yf_q = await yf_client.fetch_quote(sym)
        if yf_q is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Stock data not found for symbol {symbol}",
            )
        result = _yf_quote_to_response(sym, yf_q)
        await cache_set(cache_key, result.model_dump(mode="json"), ttl=_CACHE_TTL)
        return result

    # Non-TASE: try FMP first
    client = get_fmp_client()
    try:
        q = await _get_cached_quote(client, sym)
    except (FMPRateLimitError, FMPNotFoundError):
        q = None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching stock data: {e}",
        ) from e

    price = _safe_float((q or {}).get("price")) or 0.0

    # Fallback to yfinance if FMP returned nothing, was rate-limited, or zero price
    if q is None or price == 0:
        yf_q = await yf_client.fetch_quote(sym)
        if yf_q is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Stock data not found for symbol {symbol}",
            )
        result = _yf_quote_to_response(sym, yf_q)
        await cache_set(cache_key, result.model_dump(mode="json"), ttl=_CACHE_TTL)
        return result

    change = _safe_float(q.get("change")) or 0.0
    prev_close = _safe_float(q.get("previousClose")) or (price - change) or price
    change_pct = _safe_float(q.get("changePercentage")) or (
        (change / prev_close * 100) if prev_close > 0 else 0.0
    )

    result = StockDataResponse(
        symbol=sym,
        name=q.get("companyName") or q.get("name") or sym,
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


# ---------------------------------------------------------------------------
# Batch quote
# ---------------------------------------------------------------------------

async def fetch_stock_data_batch(symbols: list[str]) -> dict[str, StockDataResponse]:
    """Fetch stock data for multiple symbols. TASE → yfinance; others → FMP."""
    if not symbols:
        return {}
    syms = list(dict.fromkeys(s.upper() for s in symbols))[:50]

    tase_syms = [s for s in syms if _is_tase(s)]
    fmp_syms = [s for s in syms if not _is_tase(s)]

    client = get_fmp_client()
    fmp_quotes, tase_quotes = await asyncio.gather(
        asyncio.gather(*[_fetch_single_quote(client, s) for s in fmp_syms]),
        asyncio.gather(*[yf_client.fetch_quote(s) for s in tase_syms]),
    )

    out: dict[str, StockDataResponse] = {}

    for sym, q in zip(fmp_syms, fmp_quotes):
        if not q:
            continue
        price = _safe_float(q.get("price")) or 0.0
        if price == 0:
            continue
        change = _safe_float(q.get("change")) or 0.0
        prev_close = _safe_float(q.get("previousClose")) or (price - change) or price
        change_pct = _safe_float(q.get("changePercentage")) or 0.0
        out[sym] = StockDataResponse(
            symbol=sym,
            name=q.get("companyName") or q.get("name") or sym,
            current_price=round(price, 2),
            previous_close=round(prev_close, 2),
            change=round(change, 2),
            change_percent=round(change_pct, 2),
            volume=_safe_int(q.get("volume")),
            market_cap=_safe_float(q.get("marketCap")),
            currency="USD",
        )

    for sym, q in zip(tase_syms, tase_quotes):
        if not q:
            continue
        price = _safe_float(q.get("price")) or 0.0
        if price == 0:
            continue
        out[sym] = _yf_quote_to_response(sym, q)

    return out


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------

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
    """Fetch OHLCV price history. TASE → yfinance; others → FMP with yfinance fallback."""
    sym = symbol.upper()
    cache_key = f"stock_history:{sym}:{period}"
    cached = await cache_get(cache_key)
    if cached:
        return StockHistoryResponse.model_validate(cached)

    # TASE: go directly to yfinance
    if _is_tase(sym):
        rows = await yf_client.fetch_history(sym, period)
        result = _yf_history_to_response(sym, period, rows)
        await cache_set(cache_key, result.model_dump(mode="json"), ttl=_HISTORY_CACHE_TTL)
        return result

    client = get_fmp_client()
    from_date, to_date = _date_range(period)

    try:
        raw = await client.get(
            "/stable/historical-price-eod/full", {"symbol": sym, "from": from_date, "to": to_date}
        )
        items = raw if isinstance(raw, list) else (raw if isinstance(raw, dict) else {}).get("historical", [])
    except FMPRateLimitError:
        logger.warning("FMP rate limit hit for history %s/%s — falling back to yfinance", sym, period)
        items = []
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching history for {symbol}: {e}",
        ) from e

    # Fallback to yfinance if FMP returned no data or was rate-limited
    if not items:
        rows = await yf_client.fetch_history(sym, period)
        result = _yf_history_to_response(sym, period, rows)
        await cache_set(cache_key, result.model_dump(mode="json"), ttl=_HISTORY_CACHE_TTL)
        return result

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
        points.append(StockHistoryPoint(
            t=t_ms,
            o=round(float(item.get("open", 0)), 4),
            h=round(float(item.get("high", 0)), 4),
            l=round(float(item.get("low", 0)), 4),
            c=round(float(item.get("close", 0)), 4),
            v=_safe_int(item.get("volume")),
        ))

    result = StockHistoryResponse(symbol=sym, period=period, data=points)
    await cache_set(cache_key, result.model_dump(mode="json"), ttl=_HISTORY_CACHE_TTL)
    return result


# ---------------------------------------------------------------------------
# Company info
# ---------------------------------------------------------------------------

async def fetch_stock_info(symbol: str) -> StockInfoResponse:
    """Fetch detailed company info. TASE → yfinance; others → FMP with yfinance fallback."""
    sym = symbol.upper()
    cache_key = f"stock_info:{sym}"

    cached = await cache_get(cache_key)
    if cached:
        return StockInfoResponse.model_validate(cached)

    # TASE: go directly to yfinance
    if _is_tase(sym):
        yf_info = await yf_client.fetch_info(sym)
        if yf_info is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company info not found for symbol {symbol}",
            )
        result = StockInfoResponse(
            symbol=sym,
            description=yf_info.get("description"),
            website=yf_info.get("website"),
            employees=yf_info.get("employees"),
            ceo=yf_info.get("ceo"),
            country=yf_info.get("country"),
            sector=yf_info.get("sector"),
            industry=yf_info.get("industry"),
            market_cap=yf_info.get("market_cap"),
            pe_ratio=yf_info.get("pe_ratio"),
            forward_pe=yf_info.get("forward_pe"),
            beta=yf_info.get("beta"),
            dividend_yield=yf_info.get("dividend_yield"),
            fifty_two_week_high=yf_info.get("fifty_two_week_high"),
            fifty_two_week_low=yf_info.get("fifty_two_week_low"),
            average_volume=yf_info.get("average_volume"),
        )
        await cache_set(cache_key, result.model_dump(mode="json"), ttl=_INFO_CACHE_TTL)
        return result

    client = get_fmp_client()
    try:
        profile_raw, quote_raw = await asyncio.gather(
            client.get("/stable/profile", {"symbol": sym}),
            _get_cached_quote(client, sym),
            return_exceptions=True,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching info for {symbol}: {e}",
        ) from e

    p: dict = profile_raw[0] if isinstance(profile_raw, list) and profile_raw else {}
    q: dict = quote_raw if isinstance(quote_raw, dict) else {}

    # Fallback to yfinance if FMP profile is empty
    if not p:
        yf_info = await yf_client.fetch_info(sym)
        if yf_info:
            result = StockInfoResponse(
                symbol=sym,
                description=yf_info.get("description"),
                website=yf_info.get("website"),
                employees=yf_info.get("employees"),
                ceo=yf_info.get("ceo"),
                country=yf_info.get("country"),
                sector=yf_info.get("sector"),
                industry=yf_info.get("industry"),
                market_cap=yf_info.get("market_cap"),
                pe_ratio=yf_info.get("pe_ratio"),
                forward_pe=yf_info.get("forward_pe"),
                beta=yf_info.get("beta"),
                dividend_yield=yf_info.get("dividend_yield"),
                fifty_two_week_high=yf_info.get("fifty_two_week_high"),
                fifty_two_week_low=yf_info.get("fifty_two_week_low"),
                average_volume=yf_info.get("average_volume"),
            )
            await cache_set(cache_key, result.model_dump(mode="json"), ttl=_INFO_CACHE_TTL)
            return result

    employees_raw = p.get("fullTimeEmployees")
    employees: Optional[int] = None
    if employees_raw is not None:
        try:
            employees = int(str(employees_raw).replace(",", ""))
        except (ValueError, TypeError):
            pass

    market_cap = _safe_float(p.get("marketCap")) or _safe_float(p.get("mktCap")) or _safe_float(q.get("marketCap"))
    price = _safe_float(p.get("price")) or _safe_float(q.get("price"))
    last_div = _safe_float(p.get("lastDividend")) or _safe_float(p.get("lastDiv"))
    dividend_yield: Optional[float] = None
    if last_div and price and price > 0:
        dividend_yield = round(last_div / price * 100, 4)

    week52_high: Optional[float] = _safe_float(q.get("yearHigh"))
    week52_low: Optional[float] = _safe_float(q.get("yearLow"))
    if week52_high is None or week52_low is None:
        range_str = p.get("range", "")
        if range_str and "-" in str(range_str):
            try:
                parts = str(range_str).split("-")
                week52_low = week52_low or _safe_float(parts[0])
                week52_high = week52_high or _safe_float(parts[1])
            except (IndexError, ValueError):
                pass

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
        forward_pe=None,
        beta=_safe_float(p.get("beta")),
        dividend_yield=dividend_yield,
        fifty_two_week_high=week52_high,
        fifty_two_week_low=week52_low,
        average_volume=_safe_int(p.get("volAvg")) or _safe_int(p.get("averageVolume")) or _safe_int(q.get("avgVolume")),
    )

    await cache_set(cache_key, result.model_dump(mode="json"), ttl=_INFO_CACHE_TTL)
    return result


# ---------------------------------------------------------------------------
# News
# ---------------------------------------------------------------------------

async def fetch_stock_news(symbol: str, limit: int = 8) -> list[StockNewsItem]:
    """Fetch recent news. TASE → yfinance; others → FMP with yfinance fallback."""
    sym = symbol.upper()
    cache_key = f"stock_news:{sym}:{limit}"
    cached = await cache_get(cache_key)
    if cached:
        return [StockNewsItem.model_validate(r) for r in cached]

    # TASE: go directly to yfinance
    if _is_tase(sym):
        news_raw = await yf_client.fetch_news(sym, limit)
        items = [
            StockNewsItem(
                title=n["title"],
                publisher=n.get("publisher"),
                link=n.get("link"),
                published_at=n.get("published_at"),
            )
            for n in news_raw
            if n.get("title")
        ]
        if items:
            await cache_set(cache_key, [i.model_dump(mode="json") for i in items], ttl=_NEWS_CACHE_TTL)
        return items

    client = get_fmp_client()
    try:
        raw = await client.get("/stable/stock-news", {"symbol": sym, "limit": limit})
    except Exception:
        raw = []

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
        items.append(StockNewsItem(
            title=title,
            publisher=article.get("site"),
            link=article.get("url"),
            published_at=published_at,
        ))

    # Fallback to yfinance if FMP returned no news
    if not items:
        news_raw = await yf_client.fetch_news(sym, limit)
        items = [
            StockNewsItem(
                title=n["title"],
                publisher=n.get("publisher"),
                link=n.get("link"),
                published_at=n.get("published_at"),
            )
            for n in news_raw
            if n.get("title")
        ]

    if items:
        await cache_set(cache_key, [i.model_dump(mode="json") for i in items], ttl=_NEWS_CACHE_TTL)
    return items


# ---------------------------------------------------------------------------
# Dividends
# ---------------------------------------------------------------------------

async def fetch_stock_dividends(symbol: str, years: int = 5) -> StockDividendsResponse:
    """Fetch dividend history. TASE → yfinance; others → FMP with yfinance fallback."""
    sym = symbol.upper()
    cache_key = f"stock_dividends:{sym}:{years}"
    cached = await cache_get(cache_key)
    if cached:
        return StockDividendsResponse.model_validate(cached)

    cutoff = date.today() - timedelta(days=years * 365)
    one_year_ago = date.today() - timedelta(days=365)

    def _process_yf_dividends(rows: list[dict], price: Optional[float] = None) -> StockDividendsResponse:
        points: list[DividendPoint] = []
        trailing_sum = 0.0
        for row in rows:
            try:
                div_date = date.fromisoformat(row["date"][:10])
            except (KeyError, ValueError):
                continue
            if div_date < cutoff:
                continue
            amount = _safe_float(row.get("dividend"))
            if amount is None:
                continue
            t_ms = int(datetime.combine(div_date, datetime.min.time()).timestamp() * 1000)
            points.append(DividendPoint(t=t_ms, amount=round(amount, 4)))
            if div_date >= one_year_ago:
                trailing_sum += amount
        annual_yield: Optional[float] = None
        if price and price > 0 and trailing_sum > 0:
            annual_yield = round(trailing_sum / price * 100, 2)
        return StockDividendsResponse(
            symbol=sym,
            currency="ILS" if _is_tase(sym) else "USD",
            dividends=points,
            annual_yield=annual_yield,
        )

    # TASE: go directly to yfinance
    if _is_tase(sym):
        yf_q, rows = await asyncio.gather(
            yf_client.fetch_quote(sym),
            yf_client.fetch_dividends(sym, years),
        )
        price = _safe_float((yf_q or {}).get("price"))
        result = _process_yf_dividends(rows, price)
        await cache_set(cache_key, result.model_dump(mode="json"), ttl=_DIVIDENDS_CACHE_TTL)
        return result

    client = get_fmp_client()
    try:
        raw, quote_raw = await asyncio.gather(
            client.get("/stable/dividends", {"symbol": sym}),
            _get_cached_quote(client, sym),
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

    # Fallback to yfinance if FMP returned no dividend history
    if not historical:
        price: Optional[float] = None
        if isinstance(quote_raw, dict):
            price = _safe_float(quote_raw.get("price"))
        rows = await yf_client.fetch_dividends(sym, years)
        result = _process_yf_dividends(rows, price)
        await cache_set(cache_key, result.model_dump(mode="json"), ttl=_DIVIDENDS_CACHE_TTL)
        return result

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
        t_ms = int(datetime.combine(div_date, datetime.min.time()).timestamp() * 1000)
        points.append(DividendPoint(t=t_ms, amount=round(amount, 4)))
        if div_date >= one_year_ago:
            trailing_sum += amount

    # FMP returns newest-first; reverse to chronological
    points = list(reversed(points))

    annual_yield: Optional[float] = None
    price_fmp: Optional[float] = None
    if isinstance(quote_raw, dict):
        price_fmp = _safe_float(quote_raw.get("price"))
    if price_fmp and price_fmp > 0 and trailing_sum > 0:
        annual_yield = round(trailing_sum / price_fmp * 100, 2)

    result = StockDividendsResponse(
        symbol=sym,
        currency="USD",
        dividends=points,
        annual_yield=annual_yield,
    )
    await cache_set(cache_key, result.model_dump(mode="json"), ttl=_DIVIDENDS_CACHE_TTL)
    return result


# ---------------------------------------------------------------------------
# Enriched batch (52W range, avg volume, analyst rating)
# ---------------------------------------------------------------------------

async def _fetch_enriched_single(sym: str) -> StockEnrichedData:
    """Fetch enriched data for a single symbol. Uses cache with 1h TTL."""
    cache_key = f"enriched:{sym}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return StockEnrichedData.model_validate(cached)

    # Try FMP first for non-TASE (faster); yfinance for TASE or FMP fallback
    if not _is_tase(sym):
        client = get_fmp_client()
        q = await _get_cached_quote(client, sym)
        if q:
            week52_high: Optional[float] = _safe_float(q.get("yearHigh"))
            week52_low: Optional[float] = _safe_float(q.get("yearLow"))
            avg_vol: Optional[int] = _safe_int(q.get("avgVolume"))
            if week52_high or week52_low or avg_vol:
                analyst = await yf_client.fetch_recommendation(sym)
                result = StockEnrichedData(
                    symbol=sym,
                    fifty_two_week_high=week52_high,
                    fifty_two_week_low=week52_low,
                    avg_volume=avg_vol,
                    analyst_rating=analyst,
                )
                await cache_set(cache_key, result.model_dump(mode="json"), ttl=_ENRICHED_CACHE_TTL)
                return result

    # Fallback to yfinance .info for TASE and when FMP has no data
    yf_info, analyst_raw = await asyncio.gather(
        yf_client.fetch_info(sym),
        yf_client.fetch_recommendation(sym),
    )
    if yf_info:
        result = StockEnrichedData(
            symbol=sym,
            fifty_two_week_high=yf_info.get("fifty_two_week_high"),
            fifty_two_week_low=yf_info.get("fifty_two_week_low"),
            avg_volume=yf_info.get("average_volume"),
            analyst_rating=analyst_raw,
        )
        await cache_set(cache_key, result.model_dump(mode="json"), ttl=_ENRICHED_CACHE_TTL)
        return result

    result = StockEnrichedData(symbol=sym)
    await cache_set(cache_key, result.model_dump(mode="json"), ttl=_ENRICHED_CACHE_TTL)
    return result


async def fetch_stock_enriched_batch(symbols: list[str]) -> dict[str, StockEnrichedData]:
    """Fetch enriched data (52W range, avg volume, analyst rating) for multiple symbols.

    Cached 1hr per symbol. Safe to call frequently — returns stale cache if fresh.
    """
    if not symbols:
        return {}
    syms = list(dict.fromkeys(s.upper() for s in symbols))[:50]
    results = await asyncio.gather(*[_fetch_enriched_single(s) for s in syms], return_exceptions=True)
    out: dict[str, StockEnrichedData] = {}
    for sym, res in zip(syms, results):
        if isinstance(res, StockEnrichedData):
            out[sym] = res
    return out
