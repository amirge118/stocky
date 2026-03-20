import asyncio
import time

from app.agents.base import AgentResult, AgentStatus, BaseAgent
from app.core.ai_client import call_claude_json
from app.core.fmp_client import get_fmp_client


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

        # Fetch all symbols individually via FMP (concurrent)
        client = get_fmp_client()

        async def _get_quote(sym: str):
            try:
                raw = await client.get("/stable/quote", {"symbol": sym})
                items = raw if isinstance(raw, list) else []
                return items[0] if items else None
            except Exception:
                return None

        quote_results = await asyncio.gather(*[_get_quote(sym) for sym in symbols])
        all_quotes = [q for q in quote_results if q]

        stock_data: list[dict] = []
        for q in all_quotes:
            sym = q.get("symbol", "")
            price = q.get("price")
            if not sym or not price:
                continue
            price = float(price)
            change_pct = float(q.get("changePercentage") or 0)
            stock_data.append(
                {
                    "symbol": sym,
                    "price": round(price, 2),
                    "change_pct": round(change_pct, 2),
                    "volume": int(q["volume"]) if q.get("volume") else None,
                    "year_high": float(q["yearHigh"]) if q.get("yearHigh") else None,
                    "year_low": float(q["yearLow"]) if q.get("yearLow") else None,
                }
            )

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
