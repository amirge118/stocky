from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class AgentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentResult:
    agent_name: str
    agent_type: str  # "stock" | "portfolio" | "market" | "sector"
    status: AgentStatus
    data: dict = field(default_factory=dict)
    target_symbol: Optional[str] = None
    error_message: Optional[str] = None
    tokens_used: Optional[int] = None
    run_duration_ms: Optional[int] = None


class BaseAgent(ABC):
    name: str
    agent_type: str
    description: str
    schedule_cron: Optional[str] = None  # e.g. "0 8 * * 1-5"; None = on-demand only

    @abstractmethod
    async def run(self, context: dict) -> AgentResult:
        """Execute the agent and return a result."""
        ...
