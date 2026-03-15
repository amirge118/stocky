"""AI-powered stock analysis and comparison using Anthropic Claude."""

import asyncio

import anthropic
from fastapi import HTTPException, status

from app.core.cache import cache_get, cache_set
from app.core.config import settings
from app.schemas.stock import (
    StockAIAnalysisResponse,
    CompareSummaryResponse,
)
from app.services.stock_data import fetch_stock_data_from_yfinance, fetch_stock_info

_ANALYSIS_CACHE_TTL = 1800  # 30 minutes


async def generate_ai_analysis(symbol: str) -> StockAIAnalysisResponse:
    """Generate an AI-powered stock analysis using Anthropic Claude (30-min cache)."""
    sym = symbol.upper()
    cache_key = f"stock_analysis:{sym}"

    cached = await cache_get(cache_key)
    if cached:
        return StockAIAnalysisResponse.model_validate(cached)

    try:
        live_data = await fetch_stock_data_from_yfinance(sym)
    except Exception:
        live_data = None

    try:
        info = await fetch_stock_info(sym)
    except Exception:
        info = None

    price = f"${live_data.current_price:.2f}" if live_data else "N/A"
    change_pct = f"{live_data.change_percent:+.2f}%" if live_data else "N/A"
    sector = (info and info.sector) or "Unknown"
    industry = (info and info.industry) or "Unknown"
    market_cap_raw = info and info.market_cap
    if market_cap_raw and market_cap_raw >= 1e12:
        market_cap_str = f"${market_cap_raw / 1e12:.2f}T"
    elif market_cap_raw and market_cap_raw >= 1e9:
        market_cap_str = f"${market_cap_raw / 1e9:.2f}B"
    else:
        market_cap_str = "N/A"
    pe = f"{info.pe_ratio:.1f}" if (info and info.pe_ratio) else "N/A"
    hi52 = f"${info.fifty_two_week_high:.2f}" if (info and info.fifty_two_week_high) else "N/A"
    lo52 = f"${info.fifty_two_week_low:.2f}" if (info and info.fifty_two_week_low) else "N/A"

    prompt = (
        f"Provide a concise 3-4 sentence investment analysis for {sym}. "
        f"Current price: {price} ({change_pct} today). "
        f"Sector: {sector}, Industry: {industry}. "
        f"Market cap: {market_cap_str}, P/E ratio: {pe}, "
        f"52-week range: {lo52} – {hi52}. "
        "Focus on key risks, strengths, and short-term outlook. Be objective and concise."
    )

    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key or None)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        analysis_text = message.content[0].text if message.content else "Analysis unavailable."
        result = StockAIAnalysisResponse(symbol=sym, analysis=analysis_text)
        await cache_set(cache_key, result.model_dump(mode="json"), ttl=_ANALYSIS_CACHE_TTL)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating AI analysis for {symbol}: {e}",
        ) from e


async def generate_compare_summary(symbols: list[str]) -> CompareSummaryResponse:
    """Generate AI comparison summary for multiple stocks (30-min cache)."""
    if not symbols or len(symbols) > 5:
        return CompareSummaryResponse(symbols=symbols, summary="Invalid symbol list.")
    syms = [s.upper() for s in symbols[:5]]
    cache_key = f"compare_summary:{','.join(sorted(syms))}"
    cached = await cache_get(cache_key)
    if cached:
        return CompareSummaryResponse.model_validate(cached)

    data_list = await asyncio.gather(
        *[fetch_stock_data_from_yfinance(s) for s in syms],
        return_exceptions=True,
    )
    info_list = await asyncio.gather(
        *[fetch_stock_info(s) for s in syms],
        return_exceptions=True,
    )

    parts: list[str] = []
    for sym, data, info in zip(syms, data_list, info_list):
        d = data if not isinstance(data, Exception) else None
        i = info if not isinstance(info, Exception) else None
        price = f"${d.current_price:.2f}" if d else "N/A"
        chg = f"{d.change_percent:+.2f}%" if d else "N/A"
        pe = f"{i.pe_ratio:.1f}" if i and i.pe_ratio else "N/A"
        mc = "N/A"
        if i and i.market_cap:
            if i.market_cap >= 1e12:
                mc = f"${i.market_cap / 1e12:.2f}T"
            elif i.market_cap >= 1e9:
                mc = f"${i.market_cap / 1e9:.2f}B"
        sector = (i.sector or "Unknown") if i else "Unknown"
        parts.append(f"{sym}: ${price} ({chg}), P/E {pe}, MktCap {mc}, Sector {sector}")

    prompt = (
        f"Compare these {len(syms)} stocks in 2-3 concise sentences. "
        f"Focus on valuation, growth potential, and key differentiators. Be objective.\n\n"
        + "\n".join(parts)
    )

    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key or None)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        summary = message.content[0].text if message.content else "Comparison unavailable."
        result = CompareSummaryResponse(symbols=syms, summary=summary)
        await cache_set(cache_key, result.model_dump(mode="json"), ttl=_ANALYSIS_CACHE_TTL)
        return result
    except Exception as e:
        return CompareSummaryResponse(
            symbols=syms,
            summary=f"AI comparison unavailable: {str(e)[:100]}",
        )
