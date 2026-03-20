from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class NotificationSettingsResponse(BaseModel):
    id: int
    telegram_enabled: bool
    telegram_chat_id: Optional[str]
    browser_push_enabled: bool
    whatsapp_enabled: bool
    whatsapp_phone: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class NotificationSettingsUpdate(BaseModel):
    telegram_enabled: Optional[bool] = None
    telegram_chat_id: Optional[str] = None
    browser_push_enabled: Optional[bool] = None
    whatsapp_enabled: Optional[bool] = None
    whatsapp_phone: Optional[str] = None


class TestTelegramRequest(BaseModel):
    chat_id: str = Field(..., min_length=1, max_length=64)


class TestTelegramResponse(BaseModel):
    success: bool
    message: str


class TestWhatsAppRequest(BaseModel):
    phone: str = Field(..., min_length=7, max_length=32)


class TestWhatsAppResponse(BaseModel):
    success: bool
    message: str
