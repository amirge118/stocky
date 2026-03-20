from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class HealthCheck(BaseModel):
    status: str  # "ok" or "error"
    detail: Optional[str] = None

class HealthResponse(BaseModel):
    status: str  # "healthy" or "degraded"
    timestamp: datetime
    version: str = "v1"
    checks: dict[str, HealthCheck] = {}


class MessageResponse(BaseModel):
    message: str
