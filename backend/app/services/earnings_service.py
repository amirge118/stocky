"""Earnings calendar data from yfinance.

All yfinance calls are synchronous; we offload them to a thread pool via
asyncio.to_thread so they don't block the event loop.
"""

import asyncio
import logging
from datetime import date, datetime
from typing import Optional

import yfinance as yf

from app.core.cache import cache_get, cache_set
from app.schemas.earnings import EarningsEvent

logger = logging.getLogger(__name__)

_CACHE_TTL = 3600  # 1 hour — earnings dates rarely change intra-day


async def get_earnings_for_symbol(symbol: str) -> list[EarningsEvent]:
    """Fetch historical + upcoming earnings for a single symbol."""
    sym = symbol.upper()
    cache_key = f"earnings:{sym}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return [EarningsEvent(**e) for e in cached]

    def _sync() -> list[EarningsEvent]:
        ticker = yf.Ticker(sym)
        events: list[EarningsEvent] = []
        today = date.today()

        # earnings_dates: DataFrame with columns like EPS Estimate, Reported EPS, Surprise(%)
        try:
            df = ticker.earnings_dates
        except Exception:
            df = None

        if df is not None and not df.empty:
            import pandas as pd

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            for idx, row in df.iterrows():
                try:
                    if isinstance(idx, pd.Timestamp):
                        dt = idx.date()
                    elif isinstance(idx, datetime):
                        dt = idx.date()
                    else:
                        dt = date.fromisoformat(str(idx)[:10])
                except Exception:
                    continue

                eps_est = _safe_float(row.get("EPS Estimate"))
                eps_act = _safe_float(row.get("Reported EPS"))
                surprise = _safe_float(row.get("Surprise(%)"))

                is_upcoming = dt >= today
                days = (dt - today).days if is_upcoming else None

                events.append(
                    EarningsEvent(
                        symbol=sym,
                        earnings_date=dt,
                        eps_estimate=eps_est,
                        eps_actual=eps_act,
                        surprise_pct=surprise,
                        revenue_estimate=None,
                        revenue_actual=None,
                        is_upcoming=is_upcoming,
                        days_until=days,
                    )
                )

        # Try to get revenue from quarterly financials
        try:
            q_fin = ticker.quarterly_financials
            if q_fin is not None and not q_fin.empty:
                for col in q_fin.columns:
                    rev = _safe_float(q_fin.get(col, {}).get("Total Revenue"))
                    if rev is None:
                        continue
                    try:
                        fin_date = (
                            col.date()
                            if hasattr(col, "date")
                            else date.fromisoformat(str(col)[:10])
                        )
                    except Exception:
                        continue
                    # Match to existing event within 7 days
                    for ev in events:
                        if abs((ev.earnings_date - fin_date).days) <= 7:
                            ev.revenue_actual = rev
                            break
        except Exception:
            pass

        # Sort: upcoming first (ascending by date), then historical (descending)
        events.sort(
            key=lambda e: (
                not e.is_upcoming,
                -e.earnings_date.toordinal()
                if not e.is_upcoming
                else e.earnings_date.toordinal(),
            )
        )
        return events

    try:
        result = await asyncio.to_thread(_sync)
    except Exception as exc:
        logger.warning("Earnings fetch failed for %s: %s", sym, exc)
        return []

    await cache_set(
        cache_key, [e.model_dump(mode="json") for e in result], ttl=_CACHE_TTL
    )
    return result


async def get_earnings_for_symbols(symbols: list[str]) -> list[EarningsEvent]:
    """Fetch upcoming earnings for multiple symbols, merged and sorted by date."""
    tasks = [get_earnings_for_symbol(s) for s in symbols]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_events: list[EarningsEvent] = []
    for r in results:
        if isinstance(r, list):
            all_events.extend(e for e in r if e.is_upcoming)

    all_events.sort(key=lambda e: e.earnings_date)
    return all_events


def _safe_float(val: object) -> Optional[float]:
    """Coerce a value to float, returning None for NaN / missing."""
    if val is None:
        return None
    try:
        import math

        f = float(val)
        return None if math.isnan(f) else f
    except (ValueError, TypeError):
        return None
