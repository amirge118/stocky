from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification_settings import NotificationSettings
from app.schemas.notification_settings import NotificationSettingsUpdate


async def get_or_create_settings(db: AsyncSession) -> NotificationSettings:
    """Return the singleton settings row, creating it with defaults if absent."""
    result = await db.execute(
        select(NotificationSettings).where(NotificationSettings.id == 1)
    )
    row = result.scalars().first()
    if row is None:
        row = NotificationSettings(id=1)
        db.add(row)
        await db.commit()
        await db.refresh(row)
    return row


async def update_settings(
    db: AsyncSession, data: NotificationSettingsUpdate
) -> NotificationSettings:
    """Partial-update the singleton row using only the fields present in the request."""
    row = await get_or_create_settings(db)
    for field in data.model_fields_set:
        setattr(row, field, getattr(data, field))
    row.updated_at = datetime.now(tz=timezone.utc)
    await db.commit()
    await db.refresh(row)
    return row
