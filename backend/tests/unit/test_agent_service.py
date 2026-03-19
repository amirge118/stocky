"""Unit tests for agent_service."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import AgentResult, AgentStatus
from app.models.agent_report import AgentReport  # registers table with Base.metadata
from app.services import agent_service


def _result(
    agent_name: str = "stock_deep_dive",
    agent_type: str = "stock",
    status: AgentStatus = AgentStatus.COMPLETED,
    symbol: str | None = "AAPL",
) -> AgentResult:
    return AgentResult(
        agent_name=agent_name,
        agent_type=agent_type,
        status=status,
        data={"summary": "bullish"},
        target_symbol=symbol,
        tokens_used=100,
        run_duration_ms=500,
    )


def _cached_report(agent_name: str = "stock_deep_dive", symbol: str | None = "AAPL") -> dict:
    return {
        "id": 99,
        "agent_name": agent_name,
        "agent_type": "stock",
        "status": "completed",
        "target_symbol": symbol,
        "data": {"summary": "bullish"},
        "error_message": None,
        "tokens_used": 100,
        "run_duration_ms": 500,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": None,
    }


# ---------------------------------------------------------------------------
# save_agent_report
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_save_report_persists_to_db(db_session: AsyncSession):
    report = await agent_service.save_agent_report(db_session, _result())

    assert report.id is not None
    assert report.agent_name == "stock_deep_dive"
    assert report.agent_type == "stock"
    assert report.status == "completed"
    assert report.target_symbol == "AAPL"
    assert report.tokens_used == 100
    assert report.run_duration_ms == 500


@pytest.mark.asyncio
async def test_save_report_writes_to_cache(db_session: AsyncSession):
    with patch("app.services.agent_service.cache_set", new_callable=AsyncMock) as mock_set:
        await agent_service.save_agent_report(db_session, _result())

    mock_set.assert_awaited_once()
    key = mock_set.call_args[0][0]
    assert "stock_deep_dive" in key
    assert "AAPL" in key


@pytest.mark.asyncio
async def test_save_report_invalidates_stale_cache(db_session: AsyncSession):
    with patch("app.services.agent_service.cache_delete", new_callable=AsyncMock) as mock_del:
        await agent_service.save_agent_report(db_session, _result())

    mock_del.assert_awaited_once()


@pytest.mark.asyncio
async def test_save_report_without_symbol(db_session: AsyncSession):
    report = await agent_service.save_agent_report(db_session, _result(symbol=None))

    assert report.id is not None
    assert report.target_symbol is None


@pytest.mark.asyncio
async def test_save_failed_report(db_session: AsyncSession):
    failed = _result(status=AgentStatus.FAILED)
    failed.error_message = "LLM timeout"
    report = await agent_service.save_agent_report(db_session, failed)

    assert report.status == "failed"
    assert report.error_message == "LLM timeout"


# ---------------------------------------------------------------------------
# get_latest_report
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_latest_report_cache_hit(db_session: AsyncSession):
    cached = _cached_report()
    with patch("app.services.agent_service.cache_get",
               new_callable=AsyncMock, return_value=cached):
        result = await agent_service.get_latest_report(db_session, "stock_deep_dive", "AAPL")

    assert result is not None
    assert result.id == 99
    assert result.agent_name == "stock_deep_dive"
    assert result.target_symbol == "AAPL"


@pytest.mark.asyncio
async def test_get_latest_report_db_fallback(db_session: AsyncSession):
    """Cache miss falls back to DB and re-populates cache."""
    await agent_service.save_agent_report(db_session, _result())

    with (
        patch("app.services.agent_service.cache_get",
              new_callable=AsyncMock, return_value=None),
        patch("app.services.agent_service.cache_set", new_callable=AsyncMock) as mock_set,
    ):
        result = await agent_service.get_latest_report(db_session, "stock_deep_dive", "AAPL")

    assert result is not None
    assert result.agent_name == "stock_deep_dive"
    mock_set.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_latest_report_not_found(db_session: AsyncSession):
    with patch("app.services.agent_service.cache_get",
               new_callable=AsyncMock, return_value=None):
        result = await agent_service.get_latest_report(db_session, "nonexistent_agent", None)

    assert result is None


@pytest.mark.asyncio
async def test_get_latest_report_returns_most_recent(db_session: AsyncSession):
    """When multiple reports exist, the most recently created is returned."""
    for i in range(3):
        r = _result()
        r.data = {"run": i}
        await agent_service.save_agent_report(db_session, r)

    with patch("app.services.agent_service.cache_get",
               new_callable=AsyncMock, return_value=None):
        result = await agent_service.get_latest_report(db_session, "stock_deep_dive", "AAPL")

    assert result is not None
    # The most recent report has data from the last iteration
    assert result.data == {"run": 2}


# ---------------------------------------------------------------------------
# list_reports
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_reports_returns_all(db_session: AsyncSession):
    for sym in ["AAPL", "MSFT", "NVDA"]:
        await agent_service.save_agent_report(db_session, _result(symbol=sym))

    results = await agent_service.list_reports(db_session, agent_name="stock_deep_dive")
    assert len(results) == 3


@pytest.mark.asyncio
async def test_list_reports_filters_by_symbol(db_session: AsyncSession):
    await agent_service.save_agent_report(db_session, _result(symbol="AAPL"))
    await agent_service.save_agent_report(db_session, _result(symbol="MSFT"))

    results = await agent_service.list_reports(
        db_session, agent_name="stock_deep_dive", target_symbol="AAPL"
    )
    assert len(results) == 1
    assert results[0].target_symbol == "AAPL"


@pytest.mark.asyncio
async def test_list_reports_filters_by_agent_name(db_session: AsyncSession):
    await agent_service.save_agent_report(db_session, _result(agent_name="stock_deep_dive"))
    await agent_service.save_agent_report(
        db_session, _result(agent_name="market_scanner", agent_type="market", symbol=None)
    )

    results = await agent_service.list_reports(db_session, agent_name="market_scanner")
    assert len(results) == 1
    assert results[0].agent_name == "market_scanner"


@pytest.mark.asyncio
async def test_list_reports_respects_limit(db_session: AsyncSession):
    for _ in range(5):
        await agent_service.save_agent_report(db_session, _result())

    results = await agent_service.list_reports(
        db_session, agent_name="stock_deep_dive", limit=2
    )
    assert len(results) == 2


@pytest.mark.asyncio
async def test_list_reports_empty_when_no_match(db_session: AsyncSession):
    results = await agent_service.list_reports(db_session, agent_name="no_such_agent")
    assert results == []
