import time

from app.agents.base import AgentResult, AgentStatus, BaseAgent
from app.core.ai_client import call_claude_json


class PortfolioHealthAgent(BaseAgent):
    name = "portfolio_health"
    agent_type = "portfolio"
    description = "Analyzes overall portfolio health: diversification, sector concentration, risk score, and rebalancing suggestions."
    schedule_cron = "0 8 * * 1-5"  # weekdays 8am UTC

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
            from app.services.holding_service import get_portfolio
            portfolio = await get_portfolio(db)
        except Exception as e:
            return AgentResult(
                agent_name=self.name,
                agent_type=self.agent_type,
                status=AgentStatus.FAILED,
                error_message=f"Portfolio fetch error: {e}",
                run_duration_ms=int((time.time() - start) * 1000),
            )

        positions = portfolio.positions
        if not positions:
            return AgentResult(
                agent_name=self.name,
                agent_type=self.agent_type,
                status=AgentStatus.COMPLETED,
                data={"message": "No holdings in portfolio"},
                run_duration_ms=int((time.time() - start) * 1000),
            )

        total_value = portfolio.total_value or 0.0

        position_summaries = [
            f"{pos.symbol}: {pos.portfolio_pct or 0:.1f}% of portfolio, "
            f"value=${pos.current_value or 0:.0f}, "
            f"gain/loss={pos.gain_loss_pct or 0:+.1f}%"
            for pos in positions
        ]

        # HHI index of concentration
        hhi = sum((( pos.portfolio_pct or 0) / 100) ** 2 for pos in positions)

        prompt = f"""You are a portfolio risk analyst. Analyze this portfolio and return ONLY valid JSON.

Portfolio total value: ${total_value:,.0f}
Number of positions: {len(positions)}
HHI concentration index: {hhi:.3f} (0=fully diversified, 1=single stock)

Positions:
{chr(10).join(position_summaries)}

Return exactly this JSON:
{{
  "risk_score": <1-10 integer, 10=highest risk>,
  "diversification_grade": "A" | "B" | "C" | "D" | "F",
  "top_concerns": ["<concern1>", "<concern2>", "<concern3>"],
  "rebalancing_suggestions": ["<suggestion1>", "<suggestion2>"],
  "correlation_risk": "<one sentence about correlation risk>",
  "summary": "<2-3 sentence overall assessment>"
}}"""

        try:
            analysis, tokens = call_claude_json(prompt, max_tokens=500)
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
                "hhi_index": round(hhi, 4),
                "total_value": total_value,
                "num_positions": len(positions),
            },
            tokens_used=tokens,
            run_duration_ms=int((time.time() - start) * 1000),
        )
