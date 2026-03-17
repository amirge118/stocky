from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.registry import AgentRegistry
from app.core.database import get_db
from app.core.limiter import limiter
from app.schemas.agent import (
    AgentListResponse,
    AgentMeta,
    AgentReportResponse,
    TriggerResponse,
)
from app.services import agent_service

router = APIRouter()


@router.get("", response_model=AgentListResponse)
async def list_agents() -> AgentListResponse:
    """List all registered agents with metadata."""
    agents = [
        AgentMeta(
            name=a.name,
            agent_type=a.agent_type,
            description=a.description,
            schedule_cron=a.schedule_cron,
        )
        for a in AgentRegistry.all()
    ]
    return AgentListResponse(agents=agents)


async def _run_agent_task(agent_name: str, context: dict) -> None:
    """Background task: run agent and persist result in a fresh DB session."""
    import time

    from app.agents.base import AgentResult, AgentStatus
    from app.core.database import AsyncSessionLocal

    agent = AgentRegistry.get(agent_name)
    start = time.time()
    async with AsyncSessionLocal() as db:
        # Replace DB in context with fresh session
        context = {**context, "db": db}
        try:
            result = await agent.run(context)
        except Exception as e:
            result = AgentResult(
                agent_name=agent_name,
                agent_type=agent.agent_type,
                status=AgentStatus.FAILED,
                error_message=str(e),
                target_symbol=context.get("symbol"),
                run_duration_ms=int((time.time() - start) * 1000),
            )
        await agent_service.save_agent_report(db, result)


@router.post("/{agent_name}/trigger", response_model=TriggerResponse)
@limiter.limit("10/minute")
async def trigger_agent(
    request: Request,
    agent_name: str,
    background_tasks: BackgroundTasks,
    symbol: Optional[str] = None,
    sector: Optional[str] = None,
) -> TriggerResponse:
    """Manually trigger an agent run (fires in background)."""
    try:
        AgentRegistry.get(agent_name)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_name}' not found",
        ) from None

    context: dict = {}
    if symbol:
        context["symbol"] = symbol.upper()
    if sector:
        context["sector"] = sector

    background_tasks.add_task(_run_agent_task, agent_name, context)

    return TriggerResponse(
        status="triggered",
        agent_name=agent_name,
        target_symbol=symbol.upper() if symbol else None,
        message=f"Agent '{agent_name}' has been triggered and is running in the background.",
    )


@router.get("/{agent_name}/latest", response_model=Optional[AgentReportResponse])
async def get_latest_report(
    agent_name: str,
    symbol: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> Optional[AgentReportResponse]:
    """Get the most recent report for an agent (Redis-cached)."""
    try:
        AgentRegistry.get(agent_name)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_name}' not found",
        ) from None
    return await agent_service.get_latest_report(db, agent_name, symbol)


@router.get("/{agent_name}/history", response_model=list[AgentReportResponse])
async def get_agent_history(
    agent_name: str,
    symbol: Optional[str] = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> list[AgentReportResponse]:
    """Get historical runs for an agent."""
    try:
        AgentRegistry.get(agent_name)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_name}' not found",
        ) from None
    return await agent_service.list_reports(db, agent_name=agent_name, target_symbol=symbol, limit=limit)
