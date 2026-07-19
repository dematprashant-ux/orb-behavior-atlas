"""Pure Execution Domain protocol boundary without execution implementations."""

from typing import Protocol

from src.engines.execution.models import ExecutionRequest, ExecutionResult

__all__ = ["ExecutionEngine"]


class ExecutionEngine(Protocol):
    """Defines the pure contract for a future non-simulated execution engine."""

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Return a structural result without implying any execution behavior."""
