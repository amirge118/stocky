import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import anthropic
import yfinance as yf
from app.core.config import settings
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stock import Stock
from app.schemas.stock import (
    StockAIAnalysisResponse,
    StockCreate,
    StockDataResponse,
    StockHistoryPoint,
    StockHistoryResponse,
    StockInfoResponse,
    StockNewsItem,
    StockSearchResult,
    StockUpdate,
)

# Simple in-memory cache: symbol -> (data, timestamp)
_stock_data_cache: dict[str, tuple[StockDataResponse, float]] = {}
_CACHE_TTL = 300  # 5 minutes

# Cache for stock info (slow endpoint): symbol -> (data, timestamp)
_info_cache: dict[str, tuple[StockInfoResponse, float]] = {}
_INFO_CACHE_TTL = 600  # 10 minutes

# Cache for AI analysis: symbol -> (data, timestamp)
_analysis_cache: dict[str, tuple[StockAIAnalysisResponse, float]] = {}
_ANALYSIS_CACHE_TTL = 1800  # 30 minutes


async def get_stock_by_symbol(db: AsyncSession, symbol: str) -> Optional[Stock]:
    """Get a stock by its symbol."""
    result = await db.execute(
        select(Stock).where(Stock.symbol == symbol.upper())
    )
    return result.scalar_one_or_none()


async def get_stocks(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20
) -> tuple[list[Stock], int]:
    """Get list of stocks with pagination."""
    # Count total
    count_result = await db.execute(select(func.count(Stock.id)))
    total = count_result.scalar() or 0

    # Get paginated results
    result = await db.execute(
        select(Stock)
        .offset(skip)
        .limit(limit)
        .order_by(Stock.symbol)
    )
    stocks = result.scalars().all()

    return list(stocks), total


async def create_stock(db: AsyncSession, stock_data: StockCreate) -> Stock:
    """Create a new stock."""
    # Check if stock already exists
    existing = await get_stock_by_symbol(db, stock_data.symbol)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Stock with symbol {stock_data.symbol} already exists"
        )

    stock = Stock(
        symbol=stock_data.symbol.upper(),
        name=stock_data.name,
        exchange=stock_data.exchange,
        sector=stock_data.sector,
    )
    db.add(stock)
    await db.commit()
    await db.refresh(stock)
    return stock


async def update_stock(
    db: AsyncSession,
    symbol: str,
    stock_data: StockUpdate
) -> Optional[Stock]:
    """Update a stock."""
    stock = await get_stock_by_symbol(db, symbol)
    if not stock:
        return None

    update_data = stock_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(stock, key, value)

    await db.commit()
    await db.refresh(stock)
    return stock


async def delete_stock(db: AsyncSession, symbol: str) -> bool:
    """Delete a stock."""
    stock = await get_stock_by_symbol(db, symbol)
    if not stock:
        return False

    await db.delete(stock)
    await db.commit()
    return True


async def fetch_stock_data_from_yfinance(symbol: str) -> StockDataResponse:
    """Fetch live stock data from yfinance API using fast_info to avoid rate limits."""
    sym = symbol.upper()

    # Return cached data if still fresh
    if sym in _stock_data_cache:
        cached_data, cached_at = _stock_data_cache[sym]
        if time.time() - cached_at < _CACHE_TTL:
            return cached_data

    try:
        ticker = yf.Ticker(sym)
        fast_info = ticker.fast_info  # uses /v8/finance/chart/, not the rate-limited quoteSummary

        current_price = float(fast_info.last_price or 0)
        previous_close = float(fast_info.previous_close or current_price)

        if current_price == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Stock data not found for symbol {symbol}"
            )

        change = current_price - previous_close
        change_percent = (change / previous_close * 100) if previous_close > 0 else 0.0

        result = StockDataResponse(
            symbol=sym,
            name=sym,
            current_price=round(current_price, 2),
            previous_close=round(previous_close, 2),
            change=round(change, 2),
            change_percent=round(change_percent, 2),
            volume=int(fast_info.three_month_average_volume) if fast_info.three_month_average_volume else None,
            market_cap=int(fast_info.market_cap) if fast_info.market_cap else None,
            currency=fast_info.currency or "USD",
        )

        _stock_data_cache[sym] = (result, time.time())
        return result

    except HTTPException:
        raise
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "Too Many Requests" in error_str:
            # Serve stale cache rather than failing hard
            if sym in _stock_data_cache:
                return _stock_data_cache[sym][0]
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Yahoo Finance rate limit reached. Please try again in a few minutes.",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching stock data: {error_str}",
        ) from e


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

_executor = ThreadPoolExecutor(max_workers=8)


def _fetch_price_sync(symbol: str) -> Optional[float]:
    """Fetch last price synchronously (runs in executor thread)."""
    try:
        fast_info = yf.Ticker(symbol).fast_info
        price = fast_info.last_price
        return round(float(price), 2) if price else None
    except Exception:
        return None


def _fetch_currency_sync(symbol: str) -> Optional[str]:
    """Fetch currency synchronously (runs in executor thread)."""
    try:
        fast_info = yf.Ticker(symbol).fast_info
        return fast_info.currency
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


async def search_stocks_from_yfinance(query: str, limit: int = 8) -> list[StockSearchResult]:
    """Search for stocks by ticker or company name using yfinance."""
    loop = asyncio.get_event_loop()

    def _do_search() -> list[dict]:
        try:
            results = yf.Search(query.upper(), max_results=20).quotes
            return results if isinstance(results, list) else []
        except Exception:
            return []

    raw_results = await loop.run_in_executor(_executor, _do_search)

    # Filter to equities only
    equities = [r for r in raw_results if r.get("quoteType") == "EQUITY"][:limit]

    if not equities:
        return []

    # Fetch prices and sparklines in parallel
    price_tasks = [
        loop.run_in_executor(_executor, _fetch_price_sync, r["symbol"])
        for r in equities
    ]
    sparkline_tasks = [
        loop.run_in_executor(_executor, _fetch_sparkline_sync, r["symbol"])
        for r in equities
    ]
    gathered = await asyncio.gather(*price_tasks, *sparkline_tasks)
    prices = gathered[:len(equities)]
    sparklines = gathered[len(equities):]

    results: list[StockSearchResult] = []
    for item, price, sparkline in zip(equities, prices, sparklines):
        symbol = item.get("symbol", "")
        exch_code = item.get("exchange", "")
        exch_display = item.get("exchDisp", exch_code)
        country = _EXCHANGE_COUNTRY.get(exch_code)

        # Try to get currency from cache first
        currency: Optional[str] = None
        if symbol in _stock_data_cache:
            currency = _stock_data_cache[symbol][0].currency

        results.append(
            StockSearchResult(
                symbol=symbol,
                name=item.get("longname") or item.get("shortname") or symbol,
                exchange=exch_display,
                sector=item.get("sector"),
                industry=item.get("industry"),
                current_price=price,
                currency=currency,
                country=country,
                sparkline=sparkline,
            )
        )

    return results


# Period → yfinance (period, interval) mapping
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
    yf_period, yf_interval = _PERIOD_MAP.get(period, ("1mo", "1d"))
    loop = asyncio.get_event_loop()

    def _fetch() -> list[StockHistoryPoint]:
        hist = yf.Ticker(sym).history(period=yf_period, interval=yf_interval)
        if hist.empty:
            return []
        points: list[StockHistoryPoint] = []
        for ts, row in hist.iterrows():
            t_ms = int(ts.timestamp() * 1000)
            vol = row.get("Volume")
            v_int: Optional[int] = None
            if vol is not None and vol == vol:  # not NaN
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
        data = await loop.run_in_executor(_executor, _fetch)
        return StockHistoryResponse(symbol=sym, period=period, data=data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching history for {symbol}: {e}",
        ) from e


async def fetch_stock_info(symbol: str) -> StockInfoResponse:
    """Fetch detailed company info for a stock (10-min cache)."""
    sym = symbol.upper()

    if sym in _info_cache:
        cached, cached_at = _info_cache[sym]
        if time.time() - cached_at < _INFO_CACHE_TTL:
            return cached

    loop = asyncio.get_event_loop()

    def _fetch() -> dict:
        return yf.Ticker(sym).info

    try:
        info = await loop.run_in_executor(_executor, _fetch)

        # Extract CEO from companyOfficers
        ceo: Optional[str] = None
        officers = info.get("companyOfficers") or []
        for officer in officers:
            title = (officer.get("title") or "").lower()
            if "ceo" in title or "chief executive" in title:
                ceo = officer.get("name")
                break

        result = StockInfoResponse(
            symbol=sym,
            description=info.get("longBusinessSummary"),
            website=info.get("website"),
            employees=info.get("fullTimeEmployees"),
            ceo=ceo,
            country=info.get("country"),
            sector=info.get("sector"),
            industry=info.get("industry"),
            market_cap=info.get("marketCap"),
            pe_ratio=info.get("trailingPE"),
            forward_pe=info.get("forwardPE"),
            beta=info.get("beta"),
            dividend_yield=info.get("dividendYield"),
            fifty_two_week_high=info.get("fiftyTwoWeekHigh"),
            fifty_two_week_low=info.get("fiftyTwoWeekLow"),
            average_volume=info.get("averageVolume"),
        )
        _info_cache[sym] = (result, time.time())
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching info for {symbol}: {e}",
        ) from e


async def fetch_stock_news(symbol: str, limit: int = 8) -> list[StockNewsItem]:
    """Fetch recent news articles for a stock."""
    sym = symbol.upper()
    loop = asyncio.get_event_loop()

    def _fetch() -> list[dict]:
        return yf.Ticker(sym).news or []

    try:
        raw_news = await loop.run_in_executor(_executor, _fetch)
        items: list[StockNewsItem] = []
        for article in raw_news[:limit]:
            # Support both old flat schema and new nested content schema
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
                from datetime import datetime, timezone
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
        return items
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching news for {symbol}: {e}",
        ) from e


async def generate_ai_analysis(symbol: str) -> StockAIAnalysisResponse:
    """Generate an AI-powered stock analysis using Anthropic Claude (30-min cache)."""
    sym = symbol.upper()

    if sym in _analysis_cache:
        cached, cached_at = _analysis_cache[sym]
        if time.time() - cached_at < _ANALYSIS_CACHE_TTL:
            return cached

    # Gather data for the prompt
    try:
        live_data = await fetch_stock_data_from_yfinance(sym)
    except Exception:
        live_data = None

    try:
        info = await fetch_stock_info(sym)
    except Exception:
        info = None

    # Build a compact prompt
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
        _analysis_cache[sym] = (result, time.time())
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating AI analysis for {symbol}: {e}",
        ) from e
