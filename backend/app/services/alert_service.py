from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.schemas.alert import AlertCreate, AlertUpdate


async def create_alert(db: AsyncSession, data: AlertCreate) -> Alert:
    alert = Alert(
        ticker=data.ticker,
        condition_type=data.condition_type,
        target_price=data.target_price,
        is_active=True,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert


async def list_alerts(
    db: AsyncSession, limit: int = 50, offset: int = 0, ticker: Optional[str] = None
) -> list[Alert]:
    query = select(Alert)
    if ticker is not None:
        query = query.where(Alert.ticker == ticker.upper())
    query = query.order_by(Alert.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_alert(db: AsyncSession, alert_id: int) -> Optional[Alert]:
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    return result.scalars().first()


async def update_alert(
    db: AsyncSession, alert_id: int, data: AlertUpdate
) -> Optional[Alert]:
    alert = await get_alert(db, alert_id)
    if not alert:
        return None
    if data.is_active is not None:
        alert.is_active = data.is_active
    if data.target_price is not None:
        alert.target_price = data.target_price
    await db.commit()
    await db.refresh(alert)
    return alert


async def delete_alert(db: AsyncSession, alert_id: int) -> bool:
    alert = await get_alert(db, alert_id)
    if not alert:
        return False
    await db.delete(alert)
    await db.commit()
    return True


async def get_active_alerts(db: AsyncSession) -> list[Alert]:
    result = await db.execute(select(Alert).where(Alert.is_active == True))  # noqa: E712
    return list(result.scalars().all())


async def mark_triggered(db: AsyncSession, alert: Alert) -> None:
    alert.last_triggered = datetime.now(tz=timezone.utc)
    await db.commit()
