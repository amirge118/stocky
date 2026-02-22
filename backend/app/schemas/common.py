from datetime import datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str = "v1"


class MessageResponse(BaseModel):
    message: str
