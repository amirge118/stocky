from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.agents.base import BaseAgent


class AgentRegistry:
    _agents: dict[str, "BaseAgent"] = {}

    @classmethod
    def register(cls, agent: "BaseAgent") -> None:
        cls._agents[agent.name] = agent

    @classmethod
    def get(cls, name: str) -> "BaseAgent":
        agent = cls._agents.get(name)
        if agent is None:
            raise KeyError(f"Agent '{name}' not registered")
        return agent

    @classmethod
    def all(cls) -> list["BaseAgent"]:
        return list(cls._agents.values())
