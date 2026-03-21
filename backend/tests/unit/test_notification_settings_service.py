"""Unit tests for notification_settings_service."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.notification_settings import NotificationSettingsUpdate
from app.services.notification_settings_service import (
    get_or_create_settings,
    update_settings,
)

# ── get_or_create_settings ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_or_create_creates_row_on_empty_db(db_session: AsyncSession):
    """First call creates a singleton row with id=1 and returns it."""
    row = await get_or_create_settings(db_session)

    assert row is not None
    assert row.id == 1


@pytest.mark.asyncio
async def test_get_or_create_default_values(db_session: AsyncSession):
    """Newly created row has expected default values."""
    row = await get_or_create_settings(db_session)

    assert row.telegram_enabled is False
    assert row.telegram_chat_id is None
    assert row.whatsapp_enabled is False
    assert row.whatsapp_phone is None
    assert row.created_at is not None
    assert row.updated_at is None


@pytest.mark.asyncio
async def test_get_or_create_is_idempotent(db_session: AsyncSession):
    """Calling get_or_create_settings twice returns the same row — no duplicate."""
    row1 = await get_or_create_settings(db_session)
    row2 = await get_or_create_settings(db_session)

    assert row1.id == row2.id == 1


# ── update_settings ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_settings_telegram_chat_id(db_session: AsyncSession):
    """update_settings persists a changed field."""
    data = NotificationSettingsUpdate(telegram_chat_id="123456")
    row = await update_settings(db_session, data)

    assert row.telegram_chat_id == "123456"


@pytest.mark.asyncio
async def test_update_settings_partial_only_changes_set_fields(db_session: AsyncSession):
    """Fields absent from model_fields_set are left at their defaults."""
    # Set telegram_chat_id first so we have a known initial state.
    await update_settings(db_session, NotificationSettingsUpdate(telegram_chat_id="AAA"))

    # Now only update telegram_enabled — chat_id must remain "AAA".
    data = NotificationSettingsUpdate(telegram_enabled=True)
    row = await update_settings(db_session, data)

    assert row.telegram_enabled is True
    assert row.telegram_chat_id == "AAA"


@pytest.mark.asyncio
async def test_update_settings_sets_updated_at(db_session: AsyncSession):
    """update_settings stamps updated_at on every call."""
    data = NotificationSettingsUpdate(whatsapp_phone="+1234567890")
    row = await update_settings(db_session, data)

    assert row.updated_at is not None


@pytest.mark.asyncio
async def test_update_settings_whatsapp_fields(db_session: AsyncSession):
    """Both whatsapp fields can be set in a single update."""
    data = NotificationSettingsUpdate(whatsapp_enabled=True, whatsapp_phone="+9876543210")
    row = await update_settings(db_session, data)

    assert row.whatsapp_enabled is True
    assert row.whatsapp_phone == "+9876543210"
