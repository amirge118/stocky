"""Redis-backed price service with true batch yfinance fetching."""

import asyncio
import logging
from typing import List

import yfinance as yf

from app.core.cache import cache_get, cache_set
from app.core.executors import get_executor
from app.core.yf_utils import _is_rate_limited, yf_retry

logger = logging.getLogger(__name__)

_FRESH_TTL = 60       # 1 minute
_STALE_TTL = 86400    # 24 hours
_YF_TIMEOUT = 15      # seconds for batch download


def _fresh_key(ticker: str) -> str:
    return f"price:{ticker}"


def _stale_key(ticker: str) -> str:
    return f"price_stale:{ticker}"


@yf_retry
def _batch_fetch_sync(tickers: List[str]) -> dict[str, float]:
    """Run yf.download for all tickers in one call (blocking, runs in executor)."""
    df = yf.download(tickers=tickers, period="1d", progress=False, auto_adjust=True, timeout=_YF_TIMEOUT)
    if df.empty:
        return {}

    results: dict[str, float] = {}

    if len(tickers) == 1:
        # Single ticker: flat DataFrame, "Close" is a Series
        close = df["Close"]
        last = close.dropna().iloc[-1] if not close.dropna().empty else None
        if last is not None:
            results[tickers[0]] = float(last)
    else:
        # Multiple tickers: MultiIndex columns — ("Close", "TICKER")
        close = df["Close"]
        for ticker in tickers:
            if ticker not in close.columns:
                continue
            series = close[ticker].dropna()
            if not series.empty:
                results[ticker] = float(series.iloc[-1])

    return results


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
    misses = len(missing)
    logger.info(
        "PriceService cache hit rate: %d/%d (%.0f%%)",
        hits,
        total,
        hits / total * 100,
    )

    if not missing:
        return result

    # Step C — single batch fetch for all misses
    loop = asyncio.get_running_loop()
    try:
        fetched = await loop.run_in_executor(
            get_executor(), _batch_fetch_sync, missing
        )

        # Step D — write fresh + stale cache entries
        write_tasks = []
        for ticker, price in fetched.items():
            write_tasks.append(cache_set(_fresh_key(ticker), price, ttl=_FRESH_TTL))
            write_tasks.append(cache_set(_stale_key(ticker), price, ttl=_STALE_TTL))
        if write_tasks:
            await asyncio.gather(*write_tasks)

        result.update(fetched)

    except Exception as exc:
        warning_prefix = "429 / rate-limit" if _is_rate_limited(exc) else "API error"
        logger.warning("PriceService %s, falling back to stale cache: %s", warning_prefix, exc)

        stale_values = await asyncio.gather(
            *[cache_get(_stale_key(t)) for t in missing]
        )
        recovered = 0
        for ticker, value in zip(missing, stale_values):
            if value is not None:
                result[ticker] = float(value)
                recovered += 1
        logger.info("PriceService stale fallback: recovered %d/%d prices", recovered, misses)

    return result
