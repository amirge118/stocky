from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.models.alert import ConditionType


class AlertCreate(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=10)
    condition_type: ConditionType
    target_price: Decimal = Field(..., gt=0, le=1_000_000)

    @field_validator("ticker")
    @classmethod
    def uppercase_ticker(cls, v: str) -> str:
        return v.strip().upper()


class AlertUpdate(BaseModel):
    is_active: Optional[bool] = None
    target_price: Optional[Decimal] = Field(default=None, gt=0, le=1_000_000)


class AlertTriggerRequest(BaseModel):
    current_price: float = Field(..., gt=0)


class AlertResponse(BaseModel):
    id: int
    ticker: str
    condition_type: ConditionType
    target_price: Decimal
    is_active: bool
    last_triggered: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}
