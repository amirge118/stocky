"""Market overview service: indices, sector heatmap, top movers."""

import asyncio
from datetime import datetime, timezone
from typing import Optional

import yfinance as yf

from app.core.cache import cache_get, cache_set
from app.core.executors import get_executor
from app.core.yf_utils import yf_retry
from app.schemas.market import (
    IndexData,
    MarketOverviewResponse,
    MoverData,
    SectorData,
    SectorNewsItem,
)

_CACHE_TTL = 300  # 5 minutes
_YF_TIMEOUT = 10  # seconds per individual yfinance call

INDICES: dict[str, str] = {
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "Dow Jones": "^DJI",
    "VIX": "^VIX",
}

SECTORS: dict[str, str] = {
    "Technology": "XLK",
    "Financials": "XLF",
    "Health Care": "XLV",
    "Consumer Disc.": "XLY",
    "Consumer Staples": "XLP",
    "Energy": "XLE",
    "Industrials": "XLI",
    "Materials": "XLB",
    "Real Estate": "XLRE",
    "Utilities": "XLU",
    "Communication": "XLC",
}

TOP_MOVERS_UNIVERSE = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO",
    "JPM", "LLY", "V", "UNH", "XOM", "MA", "HD", "PG", "COST", "JNJ",
    "ABBV", "WMT", "AMD", "MRK", "BAC", "NFLX", "ORCL", "CRM", "CVX",
    "KO", "PEP", "TMO", "ACN", "MCD", "ADBE", "LIN", "DHR", "ABT",
    "NKE", "WFC", "TXN", "PM", "MS", "UNP", "AMGN", "RTX", "SPGI",
    "GE", "CAT", "NOW", "ISRG", "HIMS",
]


@yf_retry
def _fetch_index_sync(symbol: str, name: str) -> Optional[IndexData]:
    try:
        ticker = yf.Ticker(symbol)
        fast_info = ticker.fast_info
        if fast_info is None:
            return None
        last_price = getattr(fast_info, "last_price", None)
        previous_close = getattr(fast_info, "previous_close", None) or last_price
        if not last_price:
            return None
        price = float(last_price)
        prev = float(previous_close or price)
        change = price - prev
        change_pct = (change / prev * 100) if prev > 0 else 0.0

        hist = ticker.history(period="5d", interval="1d", timeout=_YF_TIMEOUT)
        sparkline: list[float] = []
        if not hist.empty and "Close" in hist.columns:
            closes = hist["Close"].dropna().tolist()
            sparkline = [round(float(p), 2) for p in closes]

        return IndexData(
            symbol=symbol,
            name=name,
            price=round(price, 2),
            change=round(change, 2),
            change_percent=round(change_pct, 2),
            sparkline=sparkline,
        )
    except Exception:
        return None


@yf_retry
def _fetch_sector_sync(name: str, etf: str) -> Optional[SectorData]:
    try:
        ticker = yf.Ticker(etf)
        fast_info = ticker.fast_info
        if fast_info is None:
            return None
        last_price = getattr(fast_info, "last_price", None)
        previous_close = getattr(fast_info, "previous_close", None) or last_price
        if not last_price:
            return None
        price = float(last_price)
        prev = float(previous_close or price)
        change_pct = ((price - prev) / prev * 100) if prev > 0 else 0.0

        news_items: list[SectorNewsItem] = []
        try:
            raw_news = ticker.news or []
            for item in raw_news[:2]:
                content = item.get("content", {})
                title = content.get("title") or item.get("title", "")
                url = (
                    content.get("canonicalUrl", {}).get("url")
                    or content.get("clickThroughUrl", {}).get("url")
                    or item.get("link")
                )
                publisher = content.get("provider", {}).get("displayName") or item.get("publisher")
                if title:
                    news_items.append(SectorNewsItem(title=title, url=url, publisher=publisher))
        except Exception:
            pass

        return SectorData(
            name=name,
            etf=etf,
            price=round(price, 2),
            change_percent=round(change_pct, 2),
            news=news_items,
        )
    except Exception:
        return None


@yf_retry
def _fetch_mover_sync(symbol: str) -> Optional[MoverData]:
    """Fetch mover data using fast_info only — avoids the slow .info call."""
    try:
        ticker = yf.Ticker(symbol)
        fast_info = ticker.fast_info
        if fast_info is None:
            return None
        last_price = getattr(fast_info, "last_price", None)
        previous_close = getattr(fast_info, "previous_close", None) or last_price
        if not last_price:
            return None
        price = float(last_price)
        prev = float(previous_close or price)
        change_pct = ((price - prev) / prev * 100) if prev > 0 else 0.0

        return MoverData(
            symbol=symbol,
            name=symbol,  # fast_info has no display name; symbol is used as fallback
            price=round(price, 2),
            change_percent=round(change_pct, 2),
        )
    except Exception:
        return None


async def get_market_overview() -> MarketOverviewResponse:
    """Fetch full market overview, cached for 5 minutes."""
    cache_key = "market:overview"
    cached = await cache_get(cache_key)
    if cached:
        return MarketOverviewResponse.model_validate(cached)

    loop = asyncio.get_running_loop()
    executor = get_executor()

    index_tasks = [
        loop.run_in_executor(executor, _fetch_index_sync, symbol, name)
        for name, symbol in INDICES.items()
    ]
    sector_tasks = [
        loop.run_in_executor(executor, _fetch_sector_sync, name, etf)
        for name, etf in SECTORS.items()
    ]
    mover_tasks = [
        loop.run_in_executor(executor, _fetch_mover_sync, symbol)
        for symbol in TOP_MOVERS_UNIVERSE
    ]

    index_results, sector_results, mover_results = await asyncio.gather(
        asyncio.gather(*index_tasks, return_exceptions=True),
        asyncio.gather(*sector_tasks, return_exceptions=True),
        asyncio.gather(*mover_tasks, return_exceptions=True),
    )

    indices = [r for r in index_results if isinstance(r, IndexData)]
    sectors = [r for r in sector_results if isinstance(r, SectorData)]

    movers = [r for r in mover_results if isinstance(r, MoverData)]
    movers_sorted = sorted(movers, key=lambda m: m.change_percent, reverse=True)
    gainers = movers_sorted[:5]
    losers = list(reversed(movers_sorted[-5:])) if len(movers_sorted) >= 5 else []

    response = MarketOverviewResponse(
        indices=indices,
        sectors=sectors,
        gainers=gainers,
        losers=losers,
        updated_at=datetime.now(timezone.utc).isoformat(),
    )

    await cache_set(cache_key, response.model_dump(mode="json"), ttl=_CACHE_TTL)
    return response
