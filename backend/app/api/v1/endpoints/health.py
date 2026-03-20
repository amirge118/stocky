import asyncio
from datetime import datetime

from fastapi import APIRouter

from app.schemas.common import HealthCheck, HealthResponse

router = APIRouter()

async def _check_database() -> HealthCheck:
    try:
        from app.core.database import engine
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        return HealthCheck(status="ok")
    except Exception as e:
        return HealthCheck(status="error", detail=str(e)[:100])

async def _check_redis() -> HealthCheck:
    try:
        from app.core.cache import _get_redis
        r = _get_redis()
        if r is None:
            return HealthCheck(status="ok", detail="in-memory fallback")
        await r.ping()
        return HealthCheck(status="ok")
    except Exception as e:
        return HealthCheck(status="error", detail=str(e)[:100])

@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    db_check, redis_check = await asyncio.gather(_check_database(), _check_redis())
    checks = {"database": db_check, "redis": redis_check}
    overall = "healthy" if all(c.status == "ok" for c in checks.values()) else "degraded"
    return HealthResponse(
        status=overall,
        timestamp=datetime.utcnow(),
        version="v1",
        checks=checks,
    )
