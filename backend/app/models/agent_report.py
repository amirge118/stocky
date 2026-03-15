from typing import Optional

from sqlalchemy import Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class AgentReport(BaseModel):
    """Persisted output from an AI agent run."""

    __tablename__ = "agent_reports"

    agent_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed")
    target_symbol: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, index=True)
    data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    run_duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        Index("idx_agent_reports_name_symbol_created", "agent_name", "target_symbol", "created_at"),
        Index("idx_agent_reports_type_created", "agent_type", "created_at"),
    )
