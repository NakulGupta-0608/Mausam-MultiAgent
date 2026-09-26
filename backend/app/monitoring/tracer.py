import time
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from backend.app.schemas.analysis import AgentTraceStep
from backend.app.monitoring.logger import logger


class AgentExecutionTracer:
    """Collects and records execution traces across multi-agent workflows."""

    def __init__(self, trace_id: Optional[str] = None):
        self.trace_id = trace_id or str(uuid.uuid4())
        self.steps: List[AgentTraceStep] = []
        self._start_time = time.perf_counter()

    def record_step(
        self,
        agent_name: str,
        stage: str,
        status: str,
        duration_ms: float,
        summary: str,
        inputs: Optional[Dict[str, Any]] = None,
        outputs: Optional[Dict[str, Any]] = None,
    ) -> AgentTraceStep:
        step = AgentTraceStep(
            id=str(uuid.uuid4())[:8],
            agent_name=agent_name,
            stage=stage,
            status=status,
            duration_ms=round(duration_ms, 2),
            timestamp=datetime.now(timezone.utc).isoformat(),
            summary=summary,
            inputs=inputs or {},
            outputs=outputs or {},
        )
        self.steps.append(step)
        logger.info(f"[{agent_name} -> {stage}] {status} in {step.duration_ms}ms: {summary}")
        return step

    def get_total_duration_ms(self) -> float:
        return round((time.perf_counter() - self._start_time) * 1000, 2)

    def get_steps(self) -> List[AgentTraceStep]:
        return self.steps
