import asyncio
import time
from datetime import date, timedelta
from typing import Any, Optional

from app.agents.base import AgentResult, AgentStatus, BaseAgent
from app.core.ai_client import call_claude_json
from app.core.fmp_client import get_fmp_client

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


async def _fetch_etf_performance(etf_symbol: str) -> dict:
    """Fetch 3-month and 1-year performance for an ETF from FMP historical data."""
    client = get_fmp_client()
    today = date.today()
    from_3m = (today - timedelta(days=92)).isoformat()
    from_1y = (today - timedelta(days=366)).isoformat()
    to_date = today.isoformat()

    hist_3m_raw: Any
    hist_1y_raw: Any
    hist_3m_raw, hist_1y_raw = await asyncio.gather(
        client.get(
            "/stable/historical-price-eod/full",
            {"symbol": etf_symbol, "from": from_3m, "to": to_date},
        ),
        client.get(
            "/stable/historical-price-eod/full",
            {"symbol": etf_symbol, "from": from_1y, "to": to_date},
        ),
        return_exceptions=True,
    )

    def calc_perf(raw: object) -> Optional[float]:
        if isinstance(raw, Exception):
            return None
        hist = raw if isinstance(raw, list) else (raw.get("historical", []) if isinstance(raw, dict) else [])
        if len(hist) < 2:
            return None
        # FMP returns newest-first
        last = float(hist[0]["close"])
        first = float(hist[-1]["close"])
        if first == 0:
            return None
        return round((last - first) / first * 100, 2)

    return {
        "etf": etf_symbol,
        "performance_3m": calc_perf(hist_3m_raw),
        "performance_1y": calc_perf(hist_1y_raw),
    }


class SectorTrendAgent(BaseAgent):
    name = "sector_trend"
    agent_type = "sector"
    description = "Weekly analysis of sector trends using ETF proxies and macro context."
    schedule_cron = "0 9 * * 1"  # Monday 9am UTC

    async def run(self, context: dict) -> AgentResult:
        sector: Optional[str] = context.get("sector")
        start = time.time()

        sectors_to_analyze = (
            {sector: _SECTOR_ETFS.get(sector, "SPY")} if sector else _SECTOR_ETFS
        )

        tasks = [_fetch_etf_performance(etf) for etf in sectors_to_analyze.values()]
        perf_results = await asyncio.gather(*tasks, return_exceptions=True)

        sector_perfs: dict[str, dict] = {}
        for sec, perf in zip(sectors_to_analyze.keys(), perf_results):
            if isinstance(perf, dict):
                sector_perfs[sec] = perf
            else:
                sector_perfs[sec] = {
                    "etf": _SECTOR_ETFS.get(sec, "SPY"),
                    "performance_3m": None,
                    "performance_1y": None,
                }

        def fmt_perf(val: Optional[float]) -> str:
            return "N/A" if val is None else f"{val:+.1f}%"

        sector_lines = [
            f"{sec} (ETF: {perf['etf']}): "
            f"3M={fmt_perf(perf['performance_3m'])}, "
            f"1Y={fmt_perf(perf['performance_1y'])}"
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
