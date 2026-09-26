from abc import ABC, abstractmethod
from backend.app.orchestration.state import WorkflowState
from backend.app.monitoring.tracer import AgentExecutionTracer


class BaseAgent(ABC):
    """Abstract base class for all MausamAI specialized agents."""

    def __init__(self, name: str, role: str, description: str):
        self.name = name
        self.role = role
        self.description = description

    @abstractmethod
    async def process(self, state: WorkflowState, tracer: AgentExecutionTracer) -> WorkflowState:
        """Execute the agent's task and return updated state."""
        pass
