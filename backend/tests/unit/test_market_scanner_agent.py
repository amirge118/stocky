"""Unit tests for MarketScannerAgent."""
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.base import AgentStatus
from app.agents.market_scanner import MarketScannerAgent

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_db(symbols: Optional[list[str]] = None) -> AsyncMock:
    """Return an AsyncMock DB session whose execute().fetchall() yields rows."""
    db = AsyncMock()
    rows = [(sym,) for sym in (symbols or [])]
    db_result = MagicMock()
    db_result.fetchall.return_value = rows
    db.execute.return_value = db_result
    return db


def _make_fmp_client(quotes: Optional[list[dict]] = None) -> MagicMock:
    fmp = MagicMock()
    fmp.get = AsyncMock(return_value=quotes if quotes is not None else [])
    return fmp


_QUOTE_AAPL = {
    "symbol": "AAPL",
    "price": "150.0",
    "changePercentage": "1.5",
    "volume": "1000000",
    "yearHigh": "160.0",
    "yearLow": "120.0",
}
_QUOTE_MSFT = {
    "symbol": "MSFT",
    "price": "300.0",
    "changePercentage": "-0.5",
    "volume": "500000",
    "yearHigh": "320.0",
    "yearLow": "250.0",
}

_CLAUDE_RESPONSE = {
    "top_opportunities": [],
    "top_risks": [],
    "market_mood": "NEUTRAL",
    "summary": "ok",
    "scan_date": "2024-01-01",
}


# ---------------------------------------------------------------------------
# db is None
# ---------------------------------------------------------------------------


async def test_db_none_returns_failed():
    agent = MarketScannerAgent()
    result = await agent.run({"db": None})

    assert result.status == AgentStatus.FAILED
    assert result.error_message == "Database session not available"
    assert result.agent_name == "market_scanner"
    assert result.agent_type == "market"


# ---------------------------------------------------------------------------
# DB execute raises
# ---------------------------------------------------------------------------


async def test_db_execute_raises_returns_failed():
    agent = MarketScannerAgent()
    db = AsyncMock()
    db.execute.side_effect = RuntimeError("connection refused")

    with patch("app.agents.market_scanner.get_fmp_client"):
        result = await agent.run({"db": db})

    assert result.status == AgentStatus.FAILED
    assert "DB error" in result.error_message
    assert "connection refused" in result.error_message


# ---------------------------------------------------------------------------
# No symbols in DB
# ---------------------------------------------------------------------------


async def test_no_symbols_returns_completed_with_message():
    agent = MarketScannerAgent()
    db = _make_db(symbols=[])

    with patch("app.agents.market_scanner.get_fmp_client", return_value=_make_fmp_client()):
        result = await agent.run({"db": db})

    assert result.status == AgentStatus.COMPLETED
    assert result.data == {"message": "No stocks in database to scan"}


# ---------------------------------------------------------------------------
# All FMP calls fail (return None)
# ---------------------------------------------------------------------------


async def test_all_fmp_calls_fail_returns_failed():
    agent = MarketScannerAgent()
    db = _make_db(symbols=["AAPL", "MSFT"])

    # FMP returns an empty list so every _get_quote resolves to None
    fmp_mock = _make_fmp_client(quotes=[])

    with patch("app.agents.market_scanner.get_fmp_client", return_value=fmp_mock):
        result = await agent.run({"db": db})

    assert result.status == AgentStatus.FAILED
    assert result.error_message == "Could not fetch data for any stocks"


# ---------------------------------------------------------------------------
# Success path
# ---------------------------------------------------------------------------


async def test_success_path_returns_completed_with_enriched_data():
    agent = MarketScannerAgent()
    db = _make_db(symbols=["AAPL", "MSFT"])

    # Side-effect: first call → AAPL quote, second call → MSFT quote
    fmp_mock = MagicMock()
    fmp_mock.get = AsyncMock(
        side_effect=[
            [_QUOTE_AAPL],
            [_QUOTE_MSFT],
        ]
    )

    with (
        patch("app.agents.market_scanner.get_fmp_client", return_value=fmp_mock),
        patch(
            "app.agents.market_scanner.call_claude_json",
            return_value=(_CLAUDE_RESPONSE, 100),
        ) as mock_claude,
    ):
        result = await agent.run({"db": db})

    assert result.status == AgentStatus.COMPLETED
    assert result.tokens_used == 100

    data = result.data
    assert "top_movers_up" in data
    assert "top_movers_down" in data
    assert "breakouts" in data
    assert "stocks_scanned" in data
    assert data["stocks_scanned"] == 2

    # Claude fields merged in
    assert data["market_mood"] == "NEUTRAL"
    assert data["summary"] == "ok"

    mock_claude.assert_called_once()


async def test_success_path_claude_called_with_prompt():
    """Prompt forwarded to Claude should reference the scanned symbols."""
    agent = MarketScannerAgent()
    db = _make_db(symbols=["AAPL", "MSFT"])

    fmp_mock = MagicMock()
    fmp_mock.get = AsyncMock(
        side_effect=[
            [_QUOTE_AAPL],
            [_QUOTE_MSFT],
        ]
    )

    with (
        patch("app.agents.market_scanner.get_fmp_client", return_value=fmp_mock),
        patch(
            "app.agents.market_scanner.call_claude_json",
            return_value=(_CLAUDE_RESPONSE, 50),
        ) as mock_claude,
    ):
        await agent.run({"db": db})

    prompt_arg = mock_claude.call_args[0][0]
    assert "AAPL" in prompt_arg
    assert "MSFT" in prompt_arg


async def test_breakout_detected_when_price_near_year_high():
    """A stock trading at >= 99% of its 52-week high is flagged as a breakout."""
    agent = MarketScannerAgent()
    db = _make_db(symbols=["AAPL"])

    # price 159.0 >= 160.0 * 0.99 = 158.4 → breakout
    quote_near_high = {**_QUOTE_AAPL, "price": "159.0", "yearHigh": "160.0"}
    fmp_mock = MagicMock()
    fmp_mock.get = AsyncMock(return_value=[quote_near_high])

    with (
        patch("app.agents.market_scanner.get_fmp_client", return_value=fmp_mock),
        patch(
            "app.agents.market_scanner.call_claude_json",
            return_value=(_CLAUDE_RESPONSE, 50),
        ),
    ):
        result = await agent.run({"db": db})

    assert result.status == AgentStatus.COMPLETED
    assert len(result.data["breakouts"]) == 1
    assert result.data["breakouts"][0]["symbol"] == "AAPL"


# ---------------------------------------------------------------------------
# call_claude_json raises
# ---------------------------------------------------------------------------


async def test_claude_raises_returns_failed():
    agent = MarketScannerAgent()
    db = _make_db(symbols=["AAPL", "MSFT"])

    fmp_mock = MagicMock()
    fmp_mock.get = AsyncMock(
        side_effect=[
            [_QUOTE_AAPL],
            [_QUOTE_MSFT],
        ]
    )

    with (
        patch("app.agents.market_scanner.get_fmp_client", return_value=fmp_mock),
        patch(
            "app.agents.market_scanner.call_claude_json",
            side_effect=ValueError("LLM timeout"),
        ),
    ):
        result = await agent.run({"db": db})

    assert result.status == AgentStatus.FAILED
    assert "AI analysis error" in result.error_message
    assert "LLM timeout" in result.error_message
