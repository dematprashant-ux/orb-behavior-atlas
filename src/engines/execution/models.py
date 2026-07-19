"""Immutable structural domain models for the Execution Domain."""

from dataclasses import dataclass
from enum import Enum

from src.engines.strategy.models import StrategyDecision

__all__ = [
    "ExecutionRequest",
    "ExecutionResult",
    "ExecutionStatus",
]


class ExecutionStatus(str, Enum):
    """Identifies the structural outcomes available to future execution engines."""

    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    SKIPPED = "SKIPPED"


@dataclass(frozen=True, slots=True)
class ExecutionRequest:
    """References one existing immutable strategy decision for future execution."""

    decision: StrategyDecision

    def __post_init__(self) -> None:
        """Require only the existing decision model intrinsic to a request."""
        if not isinstance(self.decision, StrategyDecision):
            raise TypeError("decision must be a StrategyDecision.")


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    """References one execution request and its structural execution status."""

    request: ExecutionRequest
    status: ExecutionStatus

    def __post_init__(self) -> None:
        """Require only the request and status types intrinsic to a result."""
        if not isinstance(self.request, ExecutionRequest):
            raise TypeError("request must be an ExecutionRequest.")
        if not isinstance(self.status, ExecutionStatus):
            raise TypeError("status must be an ExecutionStatus.")
