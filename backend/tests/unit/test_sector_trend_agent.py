"""Unit tests for SectorTrendAgent (app/agents/sector_trend.py)."""

from unittest.mock import AsyncMock, patch

from app.agents.base import AgentStatus
from app.agents.sector_trend import SectorTrendAgent

# ---------------------------------------------------------------------------
# Shared fixtures / constants
# ---------------------------------------------------------------------------

_ETF_PERF = {"etf": "XLK", "performance_3m": 5.0, "performance_1y": 20.0}

_CLAUDE_RESPONSE = (
    {
        "sectors": [],
        "summary": "ok",
        "best_sector": "Technology",
        "worst_sector": "Energy",
    },
    100,
)


# ---------------------------------------------------------------------------
# test_run_single_sector_success
# ---------------------------------------------------------------------------


async def test_run_single_sector_success():
    """Single-sector context returns COMPLETED with analysis keys in data."""
    agent = SectorTrendAgent()

    with (
        patch(
            "app.agents.sector_trend._fetch_etf_performance",
            new_callable=AsyncMock,
            return_value=_ETF_PERF,
        ),
        patch(
            "app.agents.sector_trend.call_claude_json",
            return_value=_CLAUDE_RESPONSE,
        ),
    ):
        result = await agent.run({"sector": "Technology"})

    assert result.status == AgentStatus.COMPLETED
    assert result.agent_name == "sector_trend"
    assert result.agent_type == "sector"
    assert result.target_symbol == "Technology"
    assert result.tokens_used == 100
    # Claude analysis keys must be present in data
    assert "summary" in result.data
    assert "best_sector" in result.data
    assert "worst_sector" in result.data


# ---------------------------------------------------------------------------
# test_run_all_sectors_no_context_key
# ---------------------------------------------------------------------------


async def test_run_all_sectors_no_context_key():
    """Empty context (no 'sector' key) triggers full-sector analysis and returns COMPLETED."""
    agent = SectorTrendAgent()

    with (
        patch(
            "app.agents.sector_trend._fetch_etf_performance",
            new_callable=AsyncMock,
            return_value=_ETF_PERF,
        ),
        patch(
            "app.agents.sector_trend.call_claude_json",
            return_value=_CLAUDE_RESPONSE,
        ),
    ):
        result = await agent.run({})

    assert result.status == AgentStatus.COMPLETED
    assert result.target_symbol is None


# ---------------------------------------------------------------------------
# test_run_exception_from_fetch_treated_as_none_perf
# ---------------------------------------------------------------------------


async def test_run_exception_from_fetch_treated_as_none_perf():
    """When _fetch_etf_performance raises, asyncio.gather returns the Exception object.

    The agent must handle this gracefully: the sector still appears in the
    result with None performance values and the overall run still COMPLETES.
    """
    agent = SectorTrendAgent()

    with (
        patch(
            "app.agents.sector_trend._fetch_etf_performance",
            new_callable=AsyncMock,
            side_effect=Exception("FMP unavailable"),
        ),
        patch(
            "app.agents.sector_trend.call_claude_json",
            return_value=_CLAUDE_RESPONSE,
        ),
    ):
        result = await agent.run({"sector": "Technology"})

    assert result.status == AgentStatus.COMPLETED
    # Claude still ran, so analysis keys present
    assert "summary" in result.data


# ---------------------------------------------------------------------------
# test_run_claude_raises_returns_failed
# ---------------------------------------------------------------------------


async def test_run_claude_raises_returns_failed():
    """When call_claude_json raises, the agent returns FAILED with AI analysis error."""
    agent = SectorTrendAgent()

    with (
        patch(
            "app.agents.sector_trend._fetch_etf_performance",
            new_callable=AsyncMock,
            return_value=_ETF_PERF,
        ),
        patch(
            "app.agents.sector_trend.call_claude_json",
            side_effect=Exception("ai error"),
        ),
    ):
        result = await agent.run({"sector": "Technology"})

    assert result.status == AgentStatus.FAILED
    assert result.error_message is not None
    assert "AI analysis error" in result.error_message
    assert "ai error" in result.error_message
