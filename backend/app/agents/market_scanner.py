import asyncio
import time
from typing import Optional

import yfinance as yf

from app.agents.base import AgentResult, AgentStatus, BaseAgent
from app.core.ai_client import call_claude_json
from app.core.executors import get_executor


def _fetch_fast_info_sync(symbol: str) -> Optional[dict]:
    try:
        fast_info = yf.Ticker(symbol).fast_info
        price = float(fast_info.last_price or 0)
        prev = float(fast_info.previous_close or price)
        if price == 0:
            return None
        change_pct = (price - prev) / prev * 100 if prev > 0 else 0.0
        vol = fast_info.three_month_average_volume
        return {
            "symbol": symbol,
            "price": round(price, 2),
            "change_pct": round(change_pct, 2),
            "volume": int(vol) if vol else None,
            "year_high": float(fast_info.year_high) if fast_info.year_high else None,
            "year_low": float(fast_info.year_low) if fast_info.year_low else None,
        }
    except Exception:
        return None


class MarketScannerAgent(BaseAgent):
    name = "market_scanner"
    agent_type = "market"
    description = "Scans all tracked stocks for top movers, volume spikes, and 52-week breakouts."
    schedule_cron = "30 7 * * 1-5"  # weekdays 7:30am UTC

    async def run(self, context: dict) -> AgentResult:
        db = context.get("db")
        start = time.time()

        if db is None:
            return AgentResult(
                agent_name=self.name,
                agent_type=self.agent_type,
                status=AgentStatus.FAILED,
                error_message="Database session not available",
                run_duration_ms=int((time.time() - start) * 1000),
            )

        try:
            from sqlalchemy import select

            from app.models.stock import Stock
            result = await db.execute(select(Stock.symbol))
            symbols = [row[0] for row in result.fetchall()]
        except Exception as e:
            return AgentResult(
                agent_name=self.name,
                agent_type=self.agent_type,
                status=AgentStatus.FAILED,
                error_message=f"DB error: {e}",
                run_duration_ms=int((time.time() - start) * 1000),
            )

        if not symbols:
            return AgentResult(
                agent_name=self.name,
                agent_type=self.agent_type,
                status=AgentStatus.COMPLETED,
                data={"message": "No stocks in database to scan"},
                run_duration_ms=int((time.time() - start) * 1000),
            )

        loop = asyncio.get_event_loop()
        tasks = [loop.run_in_executor(get_executor(), _fetch_fast_info_sync, sym) for sym in symbols]
        results = await asyncio.gather(*tasks)
        stock_data = [r for r in results if r is not None]

        if not stock_data:
            return AgentResult(
                agent_name=self.name,
                agent_type=self.agent_type,
                status=AgentStatus.FAILED,
                error_message="Could not fetch data for any stocks",
                run_duration_ms=int((time.time() - start) * 1000),
            )

        sorted_by_change = sorted(stock_data, key=lambda x: x["change_pct"], reverse=True)
        top_movers_up = sorted_by_change[:3]
        top_movers_down = sorted_by_change[-3:]

        breakouts = [
            s for s in stock_data
            if s.get("year_high") and s["price"] >= s["year_high"] * 0.99
        ]

        summary_lines = [
            f"{s['symbol']}: ${s['price']} ({s['change_pct']:+.1f}%)"
            for s in sorted_by_change
        ]

        prompt = f"""You are a market analyst. Review this scan of {len(stock_data)} stocks and return ONLY valid JSON.

Top gainers today: {', '.join(f"{s['symbol']} ({s['change_pct']:+.1f}%)" for s in top_movers_up)}
Top losers today: {', '.join(f"{s['symbol']} ({s['change_pct']:+.1f}%)" for s in top_movers_down)}
52-week breakouts: {', '.join(s['symbol'] for s in breakouts) or 'None'}

All stocks: {'; '.join(summary_lines)}

Return exactly this JSON:
{{
  "top_opportunities": ["<symbol: reason>", "<symbol: reason>"],
  "top_risks": ["<symbol: reason>", "<symbol: reason>"],
  "market_mood": "BULLISH" | "BEARISH" | "NEUTRAL" | "MIXED",
  "summary": "<2-3 sentence market overview>",
  "scan_date": "<today's date YYYY-MM-DD>"
}}"""

        try:
            analysis, tokens = call_claude_json(prompt, max_tokens=400)
        except Exception as e:
            return AgentResult(
                agent_name=self.name,
                agent_type=self.agent_type,
                status=AgentStatus.FAILED,
                error_message=f"AI analysis error: {e}",
                run_duration_ms=int((time.time() - start) * 1000),
            )

        return AgentResult(
            agent_name=self.name,
            agent_type=self.agent_type,
            status=AgentStatus.COMPLETED,
            data={
                **analysis,
                "top_movers_up": top_movers_up,
                "top_movers_down": top_movers_down,
                "breakouts": breakouts,
                "stocks_scanned": len(stock_data),
            },
            tokens_used=tokens,
            run_duration_ms=int((time.time() - start) * 1000),
        )
