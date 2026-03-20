"""yfinance wrapper: quote, info, history, news, dividends, TASE search.

All yfinance calls are synchronous; every public function offloads them to a
thread via asyncio.to_thread so they never block the event loop.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Optional

import yfinance as yf

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Period mapping: app period → (yfinance period, interval)
# ---------------------------------------------------------------------------
_PERIOD_MAP: dict[str, tuple[str, str]] = {
    "1d": ("1d", "5m"),
    "1w": ("5d", "30m"),
    "1m": ("1mo", "1d"),
    "6m": ("6mo", "1d"),
    "1y": ("1y", "1d"),
    "2y": ("2y", "1wk"),
    "5y": ("5y", "1wk"),
}

# ---------------------------------------------------------------------------
# TASE symbol table (~50 liquid Israeli stocks traded on TASE)
# ---------------------------------------------------------------------------
TASE_SYMBOL_TABLE: dict[str, dict] = {
    "BEZQ.TA": {"name": "Bezeq Israeli Telecom", "exchange": "TASE", "country": "Israel", "sector": "Communication Services"},
    "FIBI.TA": {"name": "First International Bank of Israel", "exchange": "TASE", "country": "Israel", "sector": "Financials"},
    "LUMI.TA": {"name": "Bank Leumi", "exchange": "TASE", "country": "Israel", "sector": "Financials"},
    "BIDI.TA": {"name": "Bank Discount", "exchange": "TASE", "country": "Israel", "sector": "Financials"},
    "HARL.TA": {"name": "Harel Insurance & Finance", "exchange": "TASE", "country": "Israel", "sector": "Financials"},
    "DSCT.TA": {"name": "Discount Investment Corporation", "exchange": "TASE", "country": "Israel", "sector": "Financials"},
    "NICE.TA": {"name": "NICE Systems", "exchange": "TASE", "country": "Israel", "sector": "Technology"},
    "CEVA.TA": {"name": "CEVA Inc.", "exchange": "TASE", "country": "Israel", "sector": "Technology"},
    "AZRG.TA": {"name": "Azrieli Group", "exchange": "TASE", "country": "Israel", "sector": "Real Estate"},
    "ICL.TA": {"name": "ICL Group", "exchange": "TASE", "country": "Israel", "sector": "Materials"},
    "TEVA.TA": {"name": "Teva Pharmaceutical", "exchange": "TASE", "country": "Israel", "sector": "Healthcare"},
    "CHKP.TA": {"name": "Check Point Software", "exchange": "TASE", "country": "Israel", "sector": "Technology"},
    "WIX.TA": {"name": "Wix.com", "exchange": "TASE", "country": "Israel", "sector": "Technology"},
    "MNDY.TA": {"name": "monday.com", "exchange": "TASE", "country": "Israel", "sector": "Technology"},
    "GLBE.TA": {"name": "Global-E Online", "exchange": "TASE", "country": "Israel", "sector": "Technology"},
    "AMOT.TA": {"name": "Amot Investments", "exchange": "TASE", "country": "Israel", "sector": "Real Estate"},
    "TASE.TA": {"name": "Tel Aviv Stock Exchange", "exchange": "TASE", "country": "Israel", "sector": "Financials"},
    "ELCO.TA": {"name": "Elco Holdings", "exchange": "TASE", "country": "Israel", "sector": "Industrials"},
    "NVMI.TA": {"name": "Nova Measuring Instruments", "exchange": "TASE", "country": "Israel", "sector": "Technology"},
    "SRAC.TA": {"name": "Strauss Group", "exchange": "TASE", "country": "Israel", "sector": "Consumer Staples"},
    "SPNS.TA": {"name": "Sapiens International", "exchange": "TASE", "country": "Israel", "sector": "Technology"},
    "ARAD.TA": {"name": "Arad Measurement", "exchange": "TASE", "country": "Israel", "sector": "Industrials"},
    "DLEKG.TA": {"name": "Delek Group", "exchange": "TASE", "country": "Israel", "sector": "Energy"},
    "SKBN.TA": {"name": "Shikun & Binui", "exchange": "TASE", "country": "Israel", "sector": "Industrials"},
    "KNFN.TA": {"name": "Kenon Holdings", "exchange": "TASE", "country": "Israel", "sector": "Industrials"},
    "IGLD.TA": {"name": "Internet Gold", "exchange": "TASE", "country": "Israel", "sector": "Communication Services"},
    "MGDL.TA": {"name": "Migdal Insurance", "exchange": "TASE", "country": "Israel", "sector": "Financials"},
    "PHOE.TA": {"name": "Phoenix Holdings", "exchange": "TASE", "country": "Israel", "sector": "Financials"},
    "ILCO.TA": {"name": "Israel Corporation", "exchange": "TASE", "country": "Israel", "sector": "Industrials"},
    "ENLT.TA": {"name": "Enlight Renewable Energy", "exchange": "TASE", "country": "Israel", "sector": "Utilities"},
    "ESLT.TA": {"name": "Elbit Systems", "exchange": "TASE", "country": "Israel", "sector": "Industrials"},
    "PTNR.TA": {"name": "Partner Communications", "exchange": "TASE", "country": "Israel", "sector": "Communication Services"},
    "HOT.TA": {"name": "Hot Telecommunication", "exchange": "TASE", "country": "Israel", "sector": "Communication Services"},
    "POLI.TA": {"name": "Bank Hapoalim", "exchange": "TASE", "country": "Israel", "sector": "Financials"},
    "BLRX.TA": {"name": "BioLineRx", "exchange": "TASE", "country": "Israel", "sector": "Healthcare"},
    "RBSN.TA": {"name": "Rosenbauer International", "exchange": "TASE", "country": "Israel", "sector": "Industrials"},
    "ADGN.TA": {"name": "AudioCodes", "exchange": "TASE", "country": "Israel", "sector": "Technology"},
    "MLSR.TA": {"name": "Malam-Team", "exchange": "TASE", "country": "Israel", "sector": "Technology"},
    "ALHE.TA": {"name": "Al Heyam Investment", "exchange": "TASE", "country": "Israel", "sector": "Real Estate"},
    "SANO.TA": {"name": "Sano", "exchange": "TASE", "country": "Israel", "sector": "Consumer Staples"},
    "NXRT.TA": {"name": "Nextar Technologies", "exchange": "TASE", "country": "Israel", "sector": "Technology"},
    "PRSK.TA": {"name": "Priortech", "exchange": "TASE", "country": "Israel", "sector": "Technology"},
}


def is_tase(symbol: str) -> bool:
    """Return True if *symbol* is traded on TASE (ends with .TA)."""
    return symbol.upper().endswith(".TA")


def search_tase(query: str, limit: int = 8) -> list[dict]:
    """Filter TASE_SYMBOL_TABLE case-insensitively by symbol or name."""
    q = query.lower()
    results: list[dict] = []
    for symbol, meta in TASE_SYMBOL_TABLE.items():
        if q in symbol.lower() or q in meta["name"].lower():
            results.append({"symbol": symbol, **meta})
            if len(results) >= limit:
                break
    return results


async def search_yf(query: str, limit: int = 8) -> list[dict]:
    """Search stocks using yfinance's built-in search (Yahoo Finance).

    Returns a list of FMP-compatible item dicts (symbol, name, stockExchange, ...).
    Returns [] on any failure or if yf.Search is unavailable.
    """
    def _sync() -> list[dict]:
        try:
            if not hasattr(yf, "Search"):
                return []
            s = yf.Search(query)
            results: list[dict] = []
            for q in (s.quotes or []):
                sym = q.get("symbol", "")
                if not sym:
                    continue
                # Exclude non-investable types
                if q.get("quoteType", "").upper() in ("CRYPTOCURRENCY", "CURRENCY", "FUTURE", "OPTION", "INDEX"):
                    continue
                results.append({
                    "symbol": sym,
                    "name": q.get("longname") or q.get("shortname") or sym,
                    "stockExchange": q.get("exchDisp") or q.get("exchange") or "",
                    "exchangeShortName": q.get("exchange") or "",
                    "currency": None,
                    "country": None,
                })
                if len(results) >= limit:
                    break
            return results
        except Exception as exc:
            logger.warning("yf.Search failed for %r: %s", query, exc)
            return []

    return await asyncio.to_thread(_sync)


def _safe_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    try:
        v = float(x)
        return None if v != v else v  # NaN → None
    except (ValueError, TypeError):
        return None


async def fetch_quote(symbol: str) -> Optional[dict]:
    """Fetch live quote using yf.Ticker.fast_info.

    Returns an FMP-compatible dict with keys:
        price, previousClose, change, changePercentage, volume, marketCap,
        currency, companyName
    Returns None on any failure.
    """
    sym = symbol.upper()

    def _sync() -> Optional[dict]:
        try:
            t = yf.Ticker(sym)
            fi = t.fast_info
            price = _safe_float(getattr(fi, "last_price", None))
            if price is None:
                return None
            prev_close = _safe_float(getattr(fi, "previous_close", None))
            change = (price - prev_close) if prev_close is not None else 0.0
            change_pct = (change / prev_close * 100) if prev_close and prev_close > 0 else 0.0
            currency = str(getattr(fi, "currency", None) or "USD")
            return {
                "price": price,
                "previousClose": prev_close,
                "change": change,
                "changePercentage": change_pct,
                "volume": _safe_float(getattr(fi, "three_month_average_volume", None)),
                "marketCap": _safe_float(getattr(fi, "market_cap", None)),
                "currency": currency,
                "companyName": sym,
            }
        except Exception as exc:
            logger.warning("yf fetch_quote failed for %s: %s", sym, exc)
            return None

    return await asyncio.to_thread(_sync)


async def fetch_info(symbol: str) -> Optional[dict]:
    """Fetch detailed company info using yf.Ticker.info.

    Returns a dict compatible with StockInfoResponse fields, or None on failure.
    """
    sym = symbol.upper()

    def _sync() -> Optional[dict]:
        try:
            raw = yf.Ticker(sym).info
            if not raw:
                return None
            price = _safe_float(raw.get("currentPrice") or raw.get("regularMarketPrice"))
            last_div = _safe_float(raw.get("lastDividendValue") or raw.get("dividendRate"))
            dividend_yield: Optional[float] = None
            if last_div and price and price > 0:
                dividend_yield = round(last_div / price * 100, 4)
            elif raw.get("dividendYield"):
                yld = _safe_float(raw.get("dividendYield"))
                if yld:
                    dividend_yield = round(yld * 100, 4)
            ceo: Optional[str] = None
            for officer in raw.get("companyOfficers", []):
                if "CEO" in (officer.get("title") or ""):
                    ceo = officer.get("name")
                    break
            employees = raw.get("fullTimeEmployees")
            return {
                "description": raw.get("longBusinessSummary"),
                "website": raw.get("website"),
                "employees": int(employees) if employees is not None else None,
                "ceo": ceo,
                "country": raw.get("country"),
                "sector": raw.get("sector"),
                "industry": raw.get("industry"),
                "market_cap": _safe_float(raw.get("marketCap")),
                "pe_ratio": _safe_float(raw.get("trailingPE")),
                "forward_pe": _safe_float(raw.get("forwardPE")),
                "beta": _safe_float(raw.get("beta")),
                "dividend_yield": dividend_yield,
                "fifty_two_week_high": _safe_float(raw.get("fiftyTwoWeekHigh")),
                "fifty_two_week_low": _safe_float(raw.get("fiftyTwoWeekLow")),
                "average_volume": raw.get("averageVolume") or raw.get("averageDailyVolume10Day"),
            }
        except Exception as exc:
            logger.warning("yf fetch_info failed for %s: %s", sym, exc)
            return None

    return await asyncio.to_thread(_sync)


async def fetch_history(symbol: str, period: str = "1m") -> list[dict]:
    """Fetch OHLCV history using yf.Ticker.history().

    Returns a list of dicts with keys: date, open, high, low, close, volume
    in chronological order.  Returns [] on any failure.
    """
    sym = symbol.upper()
    yf_period, interval = _PERIOD_MAP.get(period, ("1mo", "1d"))

    def _sync() -> list[dict]:
        try:
            df = yf.Ticker(sym).history(period=yf_period, interval=interval, auto_adjust=True)
            if df.empty:
                return []
            rows: list[dict] = []
            for row in df.itertuples():
                ts = row.Index
                try:
                    if hasattr(ts, "to_pydatetime"):
                        dt: datetime = ts.to_pydatetime()
                        if dt.tzinfo is not None:
                            dt = dt.replace(tzinfo=None)
                    else:
                        dt = datetime.combine(ts.date(), datetime.min.time())
                except Exception:
                    continue
                volume = getattr(row, "Volume", None)
                rows.append({
                    "date": dt.isoformat(),
                    "open": float(row.Open),
                    "high": float(row.High),
                    "low": float(row.Low),
                    "close": float(row.Close),
                    "volume": int(volume) if volume is not None and volume == volume else None,
                })
            return rows
        except Exception as exc:
            logger.warning("yf fetch_history failed for %s/%s: %s", sym, period, exc)
            return []

    return await asyncio.to_thread(_sync)


async def fetch_news(symbol: str, limit: int = 8) -> list[dict]:
    """Fetch recent news from yf.Ticker.news.

    Returns list of dicts with keys: title, publisher, link, published_at (Unix ms).
    Returns [] on any failure.
    """
    sym = symbol.upper()

    def _sync() -> list[dict]:
        try:
            news = yf.Ticker(sym).news or []
            items: list[dict] = []
            for article in news:
                content = article.get("content") or {}
                title = content.get("title") or article.get("title", "")
                if not title:
                    continue
                pub_time = content.get("pubDate") or article.get("providerPublishTime")
                published_at: Optional[int] = None
                if pub_time:
                    try:
                        if isinstance(pub_time, (int, float)):
                            published_at = int(pub_time * 1000)
                        else:
                            dt = datetime.fromisoformat(str(pub_time).replace("Z", ""))
                            published_at = int(dt.timestamp() * 1000)
                    except Exception:
                        pass
                provider = content.get("provider") or {}
                publisher = (provider.get("displayName") if isinstance(provider, dict) else None) or article.get("publisher", "")
                canonical = content.get("canonicalUrl") or {}
                link = (canonical.get("url") if isinstance(canonical, dict) else None) or article.get("link", "")
                items.append({
                    "title": title,
                    "publisher": publisher,
                    "link": link,
                    "published_at": published_at,
                })
                if len(items) >= limit:
                    break
            return items
        except Exception as exc:
            logger.warning("yf fetch_news failed for %s: %s", sym, exc)
            return []

    return await asyncio.to_thread(_sync)


async def fetch_recommendation(symbol: str) -> Optional[str]:
    """Fetch analyst recommendation key (e.g. 'buy', 'hold', 'sell', 'strong_buy').

    Uses yf.Ticker.info['recommendationKey'].  Returns None on any failure.
    """
    sym = symbol.upper()

    def _sync() -> Optional[str]:
        try:
            info = yf.Ticker(sym).info
            val = info.get("recommendationKey")
            return str(val).lower() if val else None
        except Exception as exc:
            logger.warning("yf fetch_recommendation failed for %s: %s", sym, exc)
            return None

    return await asyncio.to_thread(_sync)


async def fetch_dividends(symbol: str, years: int = 5) -> list[dict]:
    """Fetch dividend history from yf.Ticker.dividends.

    Returns a list of dicts with keys: date (ISO str), dividend (float),
    in chronological order.  Returns [] on any failure.
    """
    sym = symbol.upper()

    def _sync() -> list[dict]:
        try:
            series = yf.Ticker(sym).dividends
            if series is None or series.empty:
                return []
            rows: list[dict] = []
            for ts, amount in series.items():
                try:
                    d = ts.date() if hasattr(ts, "date") else ts
                    rows.append({"date": d.isoformat(), "dividend": float(amount)})
                except Exception:
                    continue
            return rows
        except Exception as exc:
            logger.warning("yf fetch_dividends failed for %s: %s", sym, exc)
            return []

    return await asyncio.to_thread(_sync)
