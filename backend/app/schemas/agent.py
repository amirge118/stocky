from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class AgentMeta(BaseModel):
    name: str
    agent_type: str
    description: str
    schedule_cron: Optional[str] = None


class AgentListResponse(BaseModel):
    agents: list[AgentMeta]


class AgentReportResponse(BaseModel):
    id: int
    agent_name: str
    agent_type: str
    status: str
    target_symbol: Optional[str] = None
    data: Optional[dict[str, Any]] = None
    error_message: Optional[str] = None
    tokens_used: Optional[int] = None
    run_duration_ms: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TriggerResponse(BaseModel):
    status: str
    agent_name: str
    target_symbol: Optional[str] = None
    message: str


class SectorSlice(BaseModel):
    sector: str
    total_value: float
    weight_pct: float
    symbols: list[str]
    num_holdings: int


class SectorBreakdownResponse(BaseModel):
    sectors: list[SectorSlice]
    total_value: float
