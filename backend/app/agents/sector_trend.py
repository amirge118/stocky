import asyncio
import time
from typing import Optional

import yfinance as yf

from app.agents.base import AgentResult, AgentStatus, BaseAgent
from app.core.ai_client import call_claude_json
from app.core.executors import get_executor

# Sector name -> ETF proxy
_SECTOR_ETFS: dict[str, str] = {
    "Technology": "XLK",
    "Energy": "XLE",
    "Health Care": "XLV",
    "Financials": "XLF",
    "Consumer Discretionary": "XLY",
    "Consumer Staples": "XLP",
    "Industrials": "XLI",
    "Materials": "XLB",
    "Real Estate": "XLRE",
    "Utilities": "XLU",
    "Communication Services": "XLC",
}


def _fetch_etf_performance_sync(etf_symbol: str) -> dict:
    try:
        ticker = yf.Ticker(etf_symbol)
        hist_3mo = ticker.history(period="3mo", interval="1d")
        hist_1y = ticker.history(period="1y", interval="1d")

        perf_3m = None
        perf_1y = None

        if not hist_3mo.empty and len(hist_3mo) >= 2:
            first = float(hist_3mo["Close"].iloc[0])
            last = float(hist_3mo["Close"].iloc[-1])
            perf_3m = round((last - first) / first * 100, 2)

        if not hist_1y.empty and len(hist_1y) >= 2:
            first = float(hist_1y["Close"].iloc[0])
            last = float(hist_1y["Close"].iloc[-1])
            perf_1y = round((last - first) / first * 100, 2)

        return {"etf": etf_symbol, "performance_3m": perf_3m, "performance_1y": perf_1y}
    except Exception:
        return {"etf": etf_symbol, "performance_3m": None, "performance_1y": None}


class SectorTrendAgent(BaseAgent):
    name = "sector_trend"
    agent_type = "sector"
    description = "Weekly analysis of sector trends using ETF proxies and macro context."
    schedule_cron = "0 9 * * 1"  # Monday 9am UTC

    async def run(self, context: dict) -> AgentResult:
        sector: Optional[str] = context.get("sector")
        start = time.time()

        sectors_to_analyze = {sector: _SECTOR_ETFS.get(sector, "SPY")} if sector else _SECTOR_ETFS

        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(get_executor(), _fetch_etf_performance_sync, etf)
            for etf in sectors_to_analyze.values()
        ]
        perf_results = await asyncio.gather(*tasks)
        sector_perfs = dict(zip(sectors_to_analyze.keys(), perf_results))

        def fmt_perf(val: Optional[float], key: str) -> str:
            return 'N/A' if val is None else f'{val:+.1f}%'

        sector_lines = [
            f"{sec} (ETF: {perf['etf']}): "
            f"3M={fmt_perf(perf['performance_3m'], '3m')}, "
            f"1Y={fmt_perf(perf['performance_1y'], '1y')}"
            for sec, perf in sector_perfs.items()
        ]

        prompt = f"""You are a macro sector analyst. Analyze sector trends and return ONLY valid JSON.

Sector ETF Performance:
{chr(10).join(sector_lines)}

Return exactly this JSON:
{{
  "sectors": [
    {{
      "sector": "<sector name>",
      "trend_direction": "UPTREND" | "DOWNTREND" | "SIDEWAYS",
      "valuation_level": "CHEAP" | "FAIR" | "EXPENSIVE",
      "macro_headwinds": "<one sentence>",
      "macro_tailwinds": "<one sentence>",
      "outlook_12m": "POSITIVE" | "NEUTRAL" | "NEGATIVE",
      "performance_3m": <number or null>,
      "performance_1y": <number or null>
    }}
  ],
  "summary": "<2-3 sentence overall sector landscape>",
  "best_sector": "<sector name>",
  "worst_sector": "<sector name>"
}}"""

        try:
            analysis, tokens = call_claude_json(prompt, max_tokens=800)
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
            target_symbol=sector,
            data=analysis,
            tokens_used=tokens,
            run_duration_ms=int((time.time() - start) * 1000),
        )
