"""Unit tests for PortfolioHealthAgent."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.base import AgentStatus
from app.agents.portfolio_health import PortfolioHealthAgent

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_portfolio(num_positions: int = 2) -> MagicMock:
    positions = []
    for i in range(num_positions):
        pos = MagicMock()
        pos.symbol = "AAPL" if i == 0 else "MSFT"
        pos.portfolio_pct = 60.0 if i == 0 else 40.0
        pos.current_value = 6000.0 if i == 0 else 4000.0
        pos.gain_loss_pct = 10.0 if i == 0 else -2.5
        positions.append(pos)

    portfolio = MagicMock()
    portfolio.positions = positions
    portfolio.total_value = 10000.0
    return portfolio


_CLAUDE_RESPONSE = {
    "risk_score": 5,
    "diversification_grade": "B",
    "top_concerns": [],
    "rebalancing_suggestions": [],
    "correlation_risk": "low",
    "summary": "ok",
}


# ---------------------------------------------------------------------------
# db is None
# ---------------------------------------------------------------------------


async def test_db_none_returns_failed():
    agent = PortfolioHealthAgent()
    result = await agent.run({"db": None})

    assert result.status == AgentStatus.FAILED
    assert result.error_message == "Database session not available"
    assert result.agent_name == "portfolio_health"
    assert result.agent_type == "portfolio"


# ---------------------------------------------------------------------------
# get_portfolio raises
# ---------------------------------------------------------------------------


async def test_get_portfolio_raises_returns_failed():
    agent = PortfolioHealthAgent()
    db = AsyncMock()

    with patch(
        "app.services.holding_service.get_portfolio",
        new_callable=AsyncMock,
        side_effect=RuntimeError("DB connection lost"),
    ):
        result = await agent.run({"db": db})

    assert result.status == AgentStatus.FAILED
    assert "Portfolio fetch error" in result.error_message
    assert "DB connection lost" in result.error_message


# ---------------------------------------------------------------------------
# Empty positions
# ---------------------------------------------------------------------------


async def test_empty_positions_returns_completed_with_message():
    agent = PortfolioHealthAgent()
    db = AsyncMock()

    empty_portfolio = MagicMock()
    empty_portfolio.positions = []
    empty_portfolio.total_value = 0.0

    with patch(
        "app.services.holding_service.get_portfolio",
        new_callable=AsyncMock,
        return_value=empty_portfolio,
    ):
        result = await agent.run({"db": db})

    assert result.status == AgentStatus.COMPLETED
    assert result.data == {"message": "No holdings in portfolio"}


# ---------------------------------------------------------------------------
# Success path
# ---------------------------------------------------------------------------


async def test_success_path_returns_completed_with_enriched_data():
    agent = PortfolioHealthAgent()
    db = AsyncMock()
    portfolio = _make_portfolio(num_positions=2)

    with (
        patch(
            "app.services.holding_service.get_portfolio",
            new_callable=AsyncMock,
            return_value=portfolio,
        ),
        patch(
            "app.agents.portfolio_health.call_claude_json",
            return_value=(_CLAUDE_RESPONSE, 100),
        ) as mock_claude,
    ):
        result = await agent.run({"db": db})

    assert result.status == AgentStatus.COMPLETED
    assert result.tokens_used == 100

    data = result.data
    assert "hhi_index" in data
    assert "total_value" in data
    assert "num_positions" in data
    assert data["total_value"] == 10000.0
    assert data["num_positions"] == 2

    # HHI = (0.6)^2 + (0.4)^2 = 0.36 + 0.16 = 0.52
    assert pytest.approx(data["hhi_index"], abs=1e-4) == 0.52

    # Claude fields merged in
    assert data["risk_score"] == 5
    assert data["diversification_grade"] == "B"

    mock_claude.assert_called_once()


async def test_success_path_claude_called_with_prompt():
    """Verify the prompt forwarded to Claude contains key portfolio information."""
    agent = PortfolioHealthAgent()
    db = AsyncMock()
    portfolio = _make_portfolio(num_positions=2)

    with (
        patch(
            "app.services.holding_service.get_portfolio",
            new_callable=AsyncMock,
            return_value=portfolio,
        ),
        patch(
            "app.agents.portfolio_health.call_claude_json",
            return_value=(_CLAUDE_RESPONSE, 50),
        ) as mock_claude,
    ):
        await agent.run({"db": db})

    prompt_arg = mock_claude.call_args[0][0]
    assert "AAPL" in prompt_arg
    assert "MSFT" in prompt_arg
    assert "10,000" in prompt_arg  # total_value formatted


# ---------------------------------------------------------------------------
# call_claude_json raises
# ---------------------------------------------------------------------------


async def test_claude_raises_returns_failed():
    agent = PortfolioHealthAgent()
    db = AsyncMock()
    portfolio = _make_portfolio()

    with (
        patch(
            "app.services.holding_service.get_portfolio",
            new_callable=AsyncMock,
            return_value=portfolio,
        ),
        patch(
            "app.agents.portfolio_health.call_claude_json",
            side_effect=ValueError("LLM timeout"),
        ),
    ):
        result = await agent.run({"db": db})

    assert result.status == AgentStatus.FAILED
    assert "AI analysis error" in result.error_message
    assert "LLM timeout" in result.error_message
