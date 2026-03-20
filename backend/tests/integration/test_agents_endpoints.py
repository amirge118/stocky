"""Integration tests for /api/v1/agents endpoints."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.agents.registry import AgentRegistry
from app.models.agent_report import AgentReport  # registers table with Base.metadata
from app.schemas.agent import AgentReportResponse


def _report_response(agent_name: str = "stock_deep_dive", symbol: str = "AAPL") -> AgentReportResponse:
    return AgentReportResponse(
        id=1,
        agent_name=agent_name,
        agent_type="stock",
        status="completed",
        target_symbol=symbol,
        data={"summary": "bullish"},
        error_message=None,
        tokens_used=150,
        run_duration_ms=800,
        created_at=datetime.now(timezone.utc),
        updated_at=None,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/agents
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_agents_returns_all_registered(client: TestClient):
    response = client.get("/api/v1/agents")

    assert response.status_code == 200
    data = response.json()
    assert "agents" in data

    registered_names = {a.name for a in AgentRegistry.all()}
    returned_names = {a["name"] for a in data["agents"]}
    assert returned_names == registered_names


@pytest.mark.asyncio
async def test_list_agents_response_shape(client: TestClient):
    response = client.get("/api/v1/agents")
    data = response.json()

    for agent in data["agents"]:
        assert "name" in agent
        assert "agent_type" in agent
        assert "description" in agent
        # schedule_cron may be null for on-demand agents


# ---------------------------------------------------------------------------
# POST /api/v1/agents/{name}/trigger
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_trigger_unknown_agent_returns_404(client: TestClient):
    response = client.post("/api/v1/agents/does_not_exist/trigger")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_trigger_known_agent_returns_triggered(client: TestClient):
    response = client.post("/api/v1/agents/stock_deep_dive/trigger?symbol=AAPL")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "triggered"
    assert data["agent_name"] == "stock_deep_dive"
    assert data["target_symbol"] == "AAPL"


@pytest.mark.asyncio
async def test_trigger_uppercases_symbol(client: TestClient):
    response = client.post("/api/v1/agents/stock_deep_dive/trigger?symbol=aapl")

    assert response.status_code == 200
    data = response.json()
    assert data["target_symbol"] == "AAPL"


@pytest.mark.asyncio
async def test_trigger_without_symbol(client: TestClient):
    response = client.post("/api/v1/agents/market_scanner/trigger")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "triggered"
    assert data["target_symbol"] is None


@pytest.mark.asyncio
async def test_trigger_includes_message(client: TestClient):
    response = client.post("/api/v1/agents/stock_deep_dive/trigger")

    data = response.json()
    assert "message" in data
    assert len(data["message"]) > 0


# ---------------------------------------------------------------------------
# GET /api/v1/agents/{name}/latest
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_latest_unknown_agent_returns_404(client: TestClient):
    response = client.get("/api/v1/agents/does_not_exist/latest")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_latest_no_reports_returns_null(client: TestClient):
    with patch(
        "app.api.v1.endpoints.agents.agent_service.get_latest_report",
        new_callable=AsyncMock,
        return_value=None,
    ):
        response = client.get("/api/v1/agents/stock_deep_dive/latest?symbol=AAPL")

    assert response.status_code == 200
    assert response.json() is None


@pytest.mark.asyncio
async def test_get_latest_returns_report_shape(client: TestClient):
    with patch(
        "app.api.v1.endpoints.agents.agent_service.get_latest_report",
        new_callable=AsyncMock,
        return_value=_report_response(),
    ):
        response = client.get("/api/v1/agents/stock_deep_dive/latest?symbol=AAPL")

    assert response.status_code == 200
    data = response.json()
    assert data["agent_name"] == "stock_deep_dive"
    assert data["status"] == "completed"
    assert data["target_symbol"] == "AAPL"
    assert "created_at" in data


# ---------------------------------------------------------------------------
# GET /api/v1/agents/{name}/history
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_history_unknown_agent_returns_404(client: TestClient):
    response = client.get("/api/v1/agents/does_not_exist/history")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_history_empty_list(client: TestClient):
    with patch(
        "app.api.v1.endpoints.agents.agent_service.list_reports",
        new_callable=AsyncMock,
        return_value=[],
    ):
        response = client.get("/api/v1/agents/stock_deep_dive/history")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_history_returns_list_of_reports(client: TestClient):
    reports = [_report_response("stock_deep_dive", "AAPL"),
               _report_response("stock_deep_dive", "MSFT")]
    with patch(
        "app.api.v1.endpoints.agents.agent_service.list_reports",
        new_callable=AsyncMock,
        return_value=reports,
    ):
        response = client.get("/api/v1/agents/stock_deep_dive/history")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["agent_name"] == "stock_deep_dive"


@pytest.mark.asyncio
async def test_get_history_passes_symbol_filter(client: TestClient):
    with patch(
        "app.api.v1.endpoints.agents.agent_service.list_reports",
        new_callable=AsyncMock,
        return_value=[_report_response()],
    ) as mock_list:
        client.get("/api/v1/agents/stock_deep_dive/history?symbol=AAPL&limit=5")

    mock_list.assert_awaited_once()
    kwargs = mock_list.call_args[1]
    assert kwargs.get("target_symbol") == "AAPL"
    assert kwargs.get("limit") == 5
