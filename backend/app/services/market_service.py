"""Market overview service: indices, sector heatmap, top movers."""

import asyncio
from datetime import datetime, timezone

from app.core.cache import cache_get, cache_set
from app.core.fmp_client import get_fmp_client
from app.schemas.market import (
    IndexData,
    MarketOverviewResponse,
    MoverData,
    SectorData,
)

_CACHE_TTL = 900  # 15 minutes — conserve API quota

INDICES: dict[str, str] = {
    "S&P 500": "SPY",
}

# Sector ETFs not supported on current FMP plan tier — kept for future upgrade
SECTORS: dict[str, str] = {}

# Trimmed to ~20 mega-cap stocks confirmed available on the FMP basic plan
TOP_MOVERS_UNIVERSE = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA",
    "JPM", "XOM", "JNJ", "WMT", "BAC", "NFLX", "AMD",
    "ORCL", "ADBE", "GE", "KO", "WFC", "MCD",
]


def _parse_quote(q: dict) -> tuple[float, float, float, float]:
    """Return (price, prev_close, change, change_pct) from an FMP quote dict."""
    price = float(q.get("price") or 0)
    prev_close = float(q.get("previousClose") or price)
    change = float(q.get("change") or (price - prev_close))
    change_pct = float(
        q.get("changePercentage") or ((change / prev_close * 100) if prev_close > 0 else 0.0)
    )
    return price, prev_close, change, change_pct


async def get_market_overview() -> MarketOverviewResponse:
    """Fetch full market overview, cached for 5 minutes."""
    cache_key = "market:overview"
    cached = await cache_get(cache_key)
    if cached:
        return MarketOverviewResponse.model_validate(cached)

    client = get_fmp_client()
    all_syms = list(dict.fromkeys(
        list(INDICES.values()) + list(SECTORS.values()) + TOP_MOVERS_UNIVERSE
    ))

    async def _get_quote(sym: str):
        try:
            raw = await client.get("/stable/quote", {"symbol": sym})
            items = raw if isinstance(raw, list) else []
            return sym, items[0] if items else None
        except Exception:
            return sym, None

    quote_results = await asyncio.gather(*[_get_quote(sym) for sym in all_syms])
    all_map = {sym: q for sym, q in quote_results if q}

    idx_map = {sym: all_map[sym] for sym in INDICES.values() if sym in all_map}
    sec_map = {sym: all_map[sym] for sym in SECTORS.values() if sym in all_map}
    mov_map = {sym: all_map[sym] for sym in TOP_MOVERS_UNIVERSE if sym in all_map}

    # Build indices
    sym_to_name = {v: k for k, v in INDICES.items()}
    indices: list[IndexData] = []
    for sym, name in sym_to_name.items():
        q = idx_map.get(sym)
        if not q:
            continue
        price, _, change, change_pct = _parse_quote(q)
        if price == 0:
            continue
        indices.append(
            IndexData(
                symbol=sym,
                name=name,
                price=round(price, 2),
                change=round(change, 2),
                change_percent=round(change_pct, 2),
                sparkline=[],
            )
        )

    # Build sectors
    sectors: list[SectorData] = []
    for name, etf in SECTORS.items():
        q = sec_map.get(etf)
        if not q:
            continue
        price, _, _, change_pct = _parse_quote(q)
        if price == 0:
            continue
        sectors.append(
            SectorData(
                name=name,
                etf=etf,
                price=round(price, 2),
                change_percent=round(change_pct, 2),
                news=[],
            )
        )

    # Build movers
    movers: list[MoverData] = []
    for sym in TOP_MOVERS_UNIVERSE:
        q = mov_map.get(sym)
        if not q:
            continue
        price, _, _, change_pct = _parse_quote(q)
        if price == 0:
            continue
        movers.append(
            MoverData(
                symbol=sym,
                name=q.get("name") or sym,
                price=round(price, 2),
                change_percent=round(change_pct, 2),
            )
        )

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
