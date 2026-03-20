"""yfinance-based historical price fetchers (free, no API key).

All yfinance calls are synchronous; we offload them to a thread pool via
asyncio.to_thread so they don't block the event loop.
"""
import asyncio
import logging
from datetime import date, datetime

import yfinance as yf

from app.core.cache import cache_get, cache_set

logger = logging.getLogger(__name__)


async def fetch_history_daily(
    symbol: str, start: date, end: date
) -> dict[date, float]:
    """Return daily close prices for *symbol* from *start* to *end* (inclusive).

    Returns an empty dict on any failure.
    """
    cache_key = f"yf_hist:{symbol}:{start.isoformat()}:{end.isoformat()}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return {date.fromisoformat(k): v for k, v in cached.items()}

    def _sync() -> dict[date, float]:
        df = yf.Ticker(symbol).history(
            start=start.isoformat(),
            end=end.isoformat(),
            interval="1d",
            auto_adjust=True,
        )
        if df.empty:
            return {}
        return {row.Index.date(): float(row["Close"]) for row in df.itertuples()}

    try:
        result = await asyncio.to_thread(_sync)
    except Exception as exc:
        logger.warning("yfinance daily fetch failed for %s: %s", symbol, exc)
        return {}

    # Cache serialises date keys as ISO strings
    await cache_set(cache_key, {k.isoformat(): v for k, v in result.items()}, ttl=3600)
    return result


async def fetch_history_intraday(
    symbol: str,
) -> list[tuple[datetime, float]]:
    """Return today's 5-minute bars for *symbol*.

    Returns an empty list on any failure.
    """
    cache_key = f"yf_intraday:{symbol}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return [(datetime.fromisoformat(ts), price) for ts, price in cached]

    def _sync() -> list[tuple[datetime, float]]:
        df = yf.Ticker(symbol).history(period="1d", interval="5m", auto_adjust=True)
        if df.empty:
            return []
        return [(r.Index.to_pydatetime(), float(r["Close"])) for r in df.itertuples()]

    try:
        result = await asyncio.to_thread(_sync)
    except Exception as exc:
        logger.warning("yfinance intraday fetch failed for %s: %s", symbol, exc)
        return []

    await cache_set(cache_key, [(ts.isoformat(), price) for ts, price in result], ttl=60)
    return result
