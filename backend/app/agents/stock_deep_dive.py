import asyncio
import time
from typing import Optional

import yfinance as yf

from app.agents.base import AgentResult, AgentStatus, BaseAgent
from app.core.ai_client import call_claude_json
from app.core.executors import get_executor


def _fetch_fundamentals_sync(symbol: str) -> dict:
    ticker = yf.Ticker(symbol)
    fast_info = ticker.fast_info
    info = ticker.info

    hist_3mo = ticker.history(period="3mo", interval="1d")
    hist_1y = ticker.history(period="1y", interval="1d")
    news = ticker.news or []

    sma_50: Optional[float] = None
    sma_200: Optional[float] = None

    if not hist_3mo.empty and len(hist_3mo) >= 50:
        sma_50 = round(float(hist_3mo["Close"].iloc[-50:].mean()), 2)
    elif not hist_3mo.empty:
        sma_50 = round(float(hist_3mo["Close"].mean()), 2)

    if not hist_1y.empty and len(hist_1y) >= 200:
        sma_200 = round(float(hist_1y["Close"].iloc[-200:].mean()), 2)
    elif not hist_1y.empty:
        sma_200 = round(float(hist_1y["Close"].mean()), 2)

    current_price = float(fast_info.last_price or 0)

    news_titles = [
        (n.get("content") or n).get("title", "") or n.get("title", "")
        for n in news[:5]
    ]

    return {
        "symbol": symbol,
        "current_price": round(current_price, 2),
        "previous_close": round(float(fast_info.previous_close or current_price), 2),
        "market_cap": int(fast_info.market_cap) if fast_info.market_cap else None,
        "pe_ratio": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "beta": info.get("beta"),
        "dividend_yield": info.get("dividendYield"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
        "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
        "revenue_growth": info.get("revenueGrowth"),
        "earnings_growth": info.get("earningsGrowth"),
        "profit_margins": info.get("profitMargins"),
        "debt_to_equity": info.get("debtToEquity"),
        "sma_50": sma_50,
        "sma_200": sma_200,
        "news_titles": [t for t in news_titles if t],
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

        loop = asyncio.get_event_loop()
        try:
            fundamentals = await loop.run_in_executor(get_executor(), _fetch_fundamentals_sync, sym)
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
            data={**analysis, "fundamentals": fundamentals, "news_titles": fundamentals.get("news_titles", [])},
            tokens_used=tokens,
            run_duration_ms=int((time.time() - start) * 1000),
        )
