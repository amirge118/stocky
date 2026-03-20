import asyncio
import time
from typing import Optional

from app.agents.base import AgentResult, AgentStatus, BaseAgent
from app.core.ai_client import call_claude_json
from app.core.fmp_client import get_fmp_client


def _sf(x: object) -> Optional[float]:
    if x is None:
        return None
    try:
        v = float(x)  # type: ignore[arg-type]
        return None if v != v else v
    except (ValueError, TypeError):
        return None


async def _fetch_fundamentals(symbol: str) -> dict:
    """Fetch fundamentals from FMP using concurrent requests."""
    client = get_fmp_client()
    quote_raw, profile_raw, news_raw = await asyncio.gather(
        client.get(f"/v3/quote/{symbol}"),
        client.get(f"/v3/profile/{symbol}"),
        client.get("/v3/stock_news", {"tickers": symbol, "limit": 5}),
        return_exceptions=True,
    )

    q: dict = quote_raw[0] if isinstance(quote_raw, list) and quote_raw else {}
    p: dict = profile_raw[0] if isinstance(profile_raw, list) and profile_raw else {}

    news_titles: list[str] = []
    if isinstance(news_raw, list):
        news_titles = [n.get("title", "") for n in news_raw[:5] if n.get("title")]

    price = float(q.get("price") or 0)
    prev = float(q.get("previousClose") or price)

    sma_50 = round(float(q["priceAvg50"]), 2) if q.get("priceAvg50") else None
    sma_200 = round(float(q["priceAvg200"]), 2) if q.get("priceAvg200") else None

    market_cap = q.get("marketCap") or p.get("mktCap")
    last_div = _sf(p.get("lastDiv"))
    div_yield = round(last_div / price, 4) if last_div and price > 0 else None

    return {
        "symbol": symbol,
        "current_price": round(price, 2),
        "previous_close": round(prev, 2),
        "market_cap": int(float(market_cap)) if market_cap else None,
        "pe_ratio": _sf(q.get("pe")),
        "forward_pe": None,
        "beta": _sf(p.get("beta")),
        "dividend_yield": div_yield,
        "sector": p.get("sector"),
        "industry": p.get("industry"),
        "fifty_two_week_high": _sf(q.get("yearHigh")),
        "fifty_two_week_low": _sf(q.get("yearLow")),
        "revenue_growth": None,
        "earnings_growth": None,
        "profit_margins": None,
        "debt_to_equity": None,
        "sma_50": sma_50,
        "sma_200": sma_200,
        "news_titles": news_titles,
    }


class StockDeepDiveAgent(BaseAgent):
    name = "stock_deep_dive"
    agent_type = "stock"
    description = "Deep-dive fundamental + technical analysis for a single stock, powered by Claude."
    schedule_cron = None  # on-demand only

    async def run(self, context: dict) -> AgentResult:
        symbol: str = context.get("symbol", "")
        if not symbol:
            return AgentResult(
                agent_name=self.name,
                agent_type=self.agent_type,
                status=AgentStatus.FAILED,
                error_message="No symbol provided in context",
            )

        sym = symbol.upper()
        start = time.time()

        try:
            fundamentals = await _fetch_fundamentals(sym)
        except Exception as e:
            return AgentResult(
                agent_name=self.name,
                agent_type=self.agent_type,
                status=AgentStatus.FAILED,
                target_symbol=sym,
                error_message=f"Data fetch error: {e}",
                run_duration_ms=int((time.time() - start) * 1000),
            )

        price = fundamentals["current_price"]
        sma_50 = fundamentals["sma_50"]
        sma_200 = fundamentals["sma_200"]
        technical_signal = "neutral"
        if price and sma_50 and sma_200:
            if price > sma_50 > sma_200:
                technical_signal = "bullish"
            elif price < sma_50 < sma_200:
                technical_signal = "bearish"

        prompt = f"""You are a senior equity analyst. Analyze {sym} and return ONLY valid JSON (no markdown).

Fundamentals:
- Price: ${price}
- Sector: {fundamentals.get('sector', 'N/A')}
- Industry: {fundamentals.get('industry', 'N/A')}
- Market Cap: {fundamentals.get('market_cap', 'N/A')}
- P/E: {fundamentals.get('pe_ratio', 'N/A')}
- Forward P/E: {fundamentals.get('forward_pe', 'N/A')}
- Beta: {fundamentals.get('beta', 'N/A')}
- Dividend Yield: {fundamentals.get('dividend_yield', 'N/A')}
- 52W High/Low: {fundamentals.get('fifty_two_week_high', 'N/A')} / {fundamentals.get('fifty_two_week_low', 'N/A')}
- Revenue Growth: {fundamentals.get('revenue_growth', 'N/A')}
- Earnings Growth: {fundamentals.get('earnings_growth', 'N/A')}
- Profit Margins: {fundamentals.get('profit_margins', 'N/A')}
- Debt/Equity: {fundamentals.get('debt_to_equity', 'N/A')}

Technicals:
- SMA-50: {sma_50}
- SMA-200: {sma_200}
- Signal: {technical_signal}

Recent news: {'; '.join(fundamentals.get('news_titles', [])) or 'N/A'}

Return exactly this JSON structure:
{{
  "recommendation": "BUY" | "HOLD" | "SELL",
  "conviction": "HIGH" | "MEDIUM" | "LOW",
  "price_target_12m": <number or null>,
  "summary": "<2-3 sentence overview>",
  "bull_case": "<1-2 sentences>",
  "bear_case": "<1-2 sentences>",
  "key_risks": ["<risk1>", "<risk2>", "<risk3>"],
  "technical_signal": "{technical_signal}",
  "sentiment": "POSITIVE" | "NEUTRAL" | "NEGATIVE"
}}"""

        try:
            analysis, tokens = call_claude_json(prompt, max_tokens=600)
        except Exception as e:
            return AgentResult(
                agent_name=self.name,
                agent_type=self.agent_type,
                status=AgentStatus.FAILED,
                target_symbol=sym,
                error_message=f"AI analysis error: {e}",
                run_duration_ms=int((time.time() - start) * 1000),
            )

        return AgentResult(
            agent_name=self.name,
            agent_type=self.agent_type,
            status=AgentStatus.COMPLETED,
            target_symbol=sym,
            data={
                **analysis,
                "fundamentals": fundamentals,
                "news_titles": fundamentals.get("news_titles", []),
            },
            tokens_used=tokens,
            run_duration_ms=int((time.time() - start) * 1000),
        )
