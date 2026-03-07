"""APScheduler integration for scheduled agent runs."""
import logging
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.agents.registry import AgentRegistry

logger = logging.getLogger(__name__)

_scheduler: Optional[AsyncIOScheduler] = None


async def _run_scheduled_agent(agent_name: str) -> None:
    """Run a scheduled agent and persist its result."""
    from app.core.database import AsyncSessionLocal
    from app.services import agent_service
    from app.agents.base import AgentResult, AgentStatus
    import time

    agent = AgentRegistry.get(agent_name)
    logger.info("Scheduler: running agent '%s'", agent_name)

    async with AsyncSessionLocal() as db:
        start = time.time()
        try:
            context = {"db": db}
            result = await agent.run(context)
        except Exception as e:
            result = AgentResult(
                agent_name=agent_name,
                agent_type=agent.agent_type,
                status=AgentStatus.FAILED,
                error_message=str(e),
                run_duration_ms=int((time.time() - start) * 1000),
            )
            logger.error("Scheduler: agent '%s' failed: %s", agent_name, e)

        await agent_service.save_agent_report(db, result)
        logger.info(
            "Scheduler: agent '%s' finished with status=%s in %dms",
            agent_name,
            result.status,
            result.run_duration_ms or 0,
        )


async def start_scheduler() -> None:
    global _scheduler
    _scheduler = AsyncIOScheduler()

    for agent in AgentRegistry.all():
        if not agent.schedule_cron:
            continue
        _scheduler.add_job(
            _run_scheduled_agent,
            trigger="cron",
            args=[agent.name],
            id=f"agent_{agent.name}",
            **_parse_cron(agent.schedule_cron),
        )
        logger.info("Scheduled agent '%s' with cron: %s", agent.name, agent.schedule_cron)

    _scheduler.start()
    logger.info("APScheduler started with %d jobs", len(_scheduler.get_jobs()))


async def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped")


def _parse_cron(cron_expr: str) -> dict:
    """Parse a 5-field cron expression into APScheduler kwargs."""
    parts = cron_expr.split()
    if len(parts) != 5:
        raise ValueError(f"Invalid cron expression: {cron_expr}")
    minute, hour, day, month, day_of_week = parts
    return {
        "minute": minute,
        "hour": hour,
        "day": day,
        "month": month,
        "day_of_week": day_of_week,
    }
