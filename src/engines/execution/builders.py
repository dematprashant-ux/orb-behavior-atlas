"""Pure construction of immutable Execution Domain request and result models."""

from src.engines.execution.models import (
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
)
from src.engines.strategy.models import StrategyDecision

__all__ = ["build_execution_request", "build_execution_result"]


def build_execution_request(decision: StrategyDecision) -> ExecutionRequest:
    """Build an execution request that retains an existing decision reference.

    Args:
        decision: Existing immutable strategy decision for future execution.

    Returns:
        An immutable request referencing ``decision``.

    Raises:
        TypeError: If ``decision`` is not a ``StrategyDecision``.
    """
    if not isinstance(decision, StrategyDecision):
        raise TypeError("decision must be a StrategyDecision.")
    return ExecutionRequest(decision=decision)


def build_execution_result(
    request: ExecutionRequest,
    status: ExecutionStatus,
) -> ExecutionResult:
    """Build an execution result that retains an existing request reference.

    Args:
        request: Existing immutable execution request.
        status: Structural status assigned by a future execution engine.

    Returns:
        An immutable result referencing ``request``.

    Raises:
        TypeError: If either input has an unsupported structural model type.
    """
    if not isinstance(request, ExecutionRequest):
        raise TypeError("request must be an ExecutionRequest.")
    if not isinstance(status, ExecutionStatus):
        raise TypeError("status must be an ExecutionStatus.")
    return ExecutionResult(request=request, status=status)
