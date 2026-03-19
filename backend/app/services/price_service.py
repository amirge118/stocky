"""Redis-backed price service using FMP batch quote endpoint."""

import asyncio
import logging
from typing import List

from app.core.cache import cache_get, cache_set
from app.core.fmp_client import FMPRateLimitError, get_fmp_client

logger = logging.getLogger(__name__)

_FRESH_TTL = 300      # 5 minutes — conserve API quota
_STALE_TTL = 86400    # 24 hours


def _fresh_key(ticker: str) -> str:
    return f"price:{ticker}"


def _stale_key(ticker: str) -> str:
    return f"price_stale:{ticker}"


async def get_prices(tickers: List[str]) -> dict[str, float]:
    """Return latest prices for *tickers*, using Redis cache with stale fallback.

    Cache strategy:
    - Fresh key  price:{TICKER}       TTL 60s  — primary cache
    - Stale key  price_stale:{TICKER} TTL 24h  — fallback on API failure
    """
    tickers = list(dict.fromkeys(t.upper() for t in tickers))
    if not tickers:
        return {}

    # Step A — parallel Redis lookups
    cached_values = await asyncio.gather(
        *[cache_get(_fresh_key(t)) for t in tickers]
    )

    result: dict[str, float] = {}
    for ticker, value in zip(tickers, cached_values):
        if value is not None:
            result[ticker] = float(value)

    # Step B — identify misses
    missing = [t for t in tickers if t not in result]

    total = len(tickers)
    hits = len(result)
    logger.info(
        "PriceService cache hit rate: %d/%d (%.0f%%)",
        hits,
        total,
        hits / total * 100,
    )

    if not missing:
        return result

    # Step C — individual concurrent fetches from FMP for all misses
    client = get_fmp_client()
    try:
        async def _get_price(sym: str):
            raw = await client.get("/stable/quote", {"symbol": sym})
            items = raw if isinstance(raw, list) else []
            return sym, items[0] if items else None

        price_results = await asyncio.gather(*[_get_price(sym) for sym in missing])

        fetched: dict[str, float] = {}
        for sym, q in price_results:
            if q is None:
                continue
            price = q.get("price")
            if price is not None:
                try:
                    fetched[sym] = float(price)
                except (ValueError, TypeError):
                    pass

        # Step D — write fresh + stale cache entries
        write_tasks = []
        for ticker, price in fetched.items():
            write_tasks.append(cache_set(_fresh_key(ticker), price, ttl=_FRESH_TTL))
            write_tasks.append(cache_set(_stale_key(ticker), price, ttl=_STALE_TTL))
        if write_tasks:
            await asyncio.gather(*write_tasks)

        result.update(fetched)

    except Exception as exc:
        warning_prefix = "rate-limit" if isinstance(exc, FMPRateLimitError) else "API error"
        logger.warning(
            "PriceService %s, falling back to stale cache: %s", warning_prefix, exc
        )

        stale_values = await asyncio.gather(
            *[cache_get(_stale_key(t)) for t in missing]
        )
        recovered = 0
        for ticker, value in zip(missing, stale_values):
            if value is not None:
                result[ticker] = float(value)
                recovered += 1
        logger.info(
            "PriceService stale fallback: recovered %d/%d prices",
            recovered,
            len(missing),
        )

    return result
