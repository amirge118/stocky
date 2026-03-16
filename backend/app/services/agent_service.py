from typing import Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import AgentResult
from app.core.cache import cache_delete, cache_get, cache_set
from app.models.agent_report import AgentReport
from app.schemas.agent import AgentReportResponse

_REPORT_TTL = 3600  # 1 hour


def _cache_key(agent_name: str, target_symbol: Optional[str] = None) -> str:
    if target_symbol:
        return f"agent_report:{agent_name}:{target_symbol.upper()}"
    return f"agent_report:{agent_name}"


async def save_agent_report(db: AsyncSession, result: AgentResult) -> AgentReport:
    """Persist agent result to PostgreSQL and update Redis cache."""
    report = AgentReport(
        agent_name=result.agent_name,
        agent_type=result.agent_type,
        status=result.status.value,
        target_symbol=result.target_symbol,
        data=result.data,
        error_message=result.error_message,
        tokens_used=result.tokens_used,
        run_duration_ms=result.run_duration_ms,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    # Invalidate cache so next read picks up fresh data
    key = _cache_key(result.agent_name, result.target_symbol)
    await cache_delete(key)

    # Pre-populate cache with new result
    response = AgentReportResponse.model_validate(report)
    await cache_set(key, response.model_dump(mode="json"), ttl=_REPORT_TTL)

    return report


async def get_latest_report(
    db: AsyncSession,
    agent_name: str,
    target_symbol: Optional[str] = None,
) -> Optional[AgentReportResponse]:
    """Return the latest report, checking Redis first."""
    key = _cache_key(agent_name, target_symbol)
    cached = await cache_get(key)
    if cached:
        return AgentReportResponse.model_validate(cached)

    # Fallback to DB
    q = (
        select(AgentReport)
        .where(AgentReport.agent_name == agent_name)
        .order_by(desc(AgentReport.created_at))
        .limit(1)
    )
    if target_symbol:
        q = q.where(AgentReport.target_symbol == target_symbol.upper())

    result = await db.execute(q)
    report = result.scalar_one_or_none()
    if report is None:
        return None

    response = AgentReportResponse.model_validate(report)
    await cache_set(key, response.model_dump(mode="json"), ttl=_REPORT_TTL)
    return response


async def list_reports(
    db: AsyncSession,
    agent_name: Optional[str] = None,
    agent_type: Optional[str] = None,
    target_symbol: Optional[str] = None,
    limit: int = 20,
) -> list[AgentReportResponse]:
    """List historical agent reports with optional filters."""
    q = select(AgentReport).order_by(desc(AgentReport.created_at)).limit(limit)
    if agent_name:
        q = q.where(AgentReport.agent_name == agent_name)
    if agent_type:
        q = q.where(AgentReport.agent_type == agent_type)
    if target_symbol:
        q = q.where(AgentReport.target_symbol == target_symbol.upper())

    result = await db.execute(q)
    reports = result.scalars().all()
    return [AgentReportResponse.model_validate(r) for r in reports]
