from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.limiter import limiter
from app.core.telegram import send_test_message
from app.core.whatsapp import send_test_whatsapp_message
from app.schemas.notification_settings import (
    NotificationSettingsResponse,
    NotificationSettingsUpdate,
    TestTelegramRequest,
    TestTelegramResponse,
    TestWhatsAppRequest,
    TestWhatsAppResponse,
)
from app.services.notification_settings_service import (
    get_or_create_settings,
    update_settings,
)

router = APIRouter()


@router.get("/notifications", response_model=NotificationSettingsResponse)
async def get_notification_settings(
    db: AsyncSession = Depends(get_db),
) -> NotificationSettingsResponse:
    """Return current notification settings (creates defaults on first call)."""
    row = await get_or_create_settings(db)
    return NotificationSettingsResponse.model_validate(row)


@router.patch("/notifications", response_model=NotificationSettingsResponse)
async def update_notification_settings(
    data: NotificationSettingsUpdate,
    db: AsyncSession = Depends(get_db),
) -> NotificationSettingsResponse:
    """Partially update notification settings."""
    row = await update_settings(db, data)
    return NotificationSettingsResponse.model_validate(row)


@router.post("/notifications/test/telegram", response_model=TestTelegramResponse)
@limiter.limit("5/minute")
async def test_telegram_connection(
    request: Request,
    body: TestTelegramRequest,
    db: AsyncSession = Depends(get_db),
) -> TestTelegramResponse:
    """Send a test Telegram message to verify the chat ID is working."""
    success, message = await send_test_message(body.chat_id)
    return TestTelegramResponse(success=success, message=message)


@router.post("/notifications/test/whatsapp", response_model=TestWhatsAppResponse)
@limiter.limit("5/minute")
async def test_whatsapp_connection(
    request: Request,
    body: TestWhatsAppRequest,
    db: AsyncSession = Depends(get_db),
) -> TestWhatsAppResponse:
    """Send a test WhatsApp message to verify the phone number is working."""
    success, message = await send_test_whatsapp_message(body.phone)
    return TestWhatsAppResponse(success=success, message=message)
