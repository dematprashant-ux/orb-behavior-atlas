"""Immutable structural domain models for the Execution Domain."""

from dataclasses import dataclass
from enum import Enum
from math import isfinite

from src.engines.strategy.models import StrategyDecision

__all__ = [
    "CompletedTrade",
    "ExecutionRequest",
    "ExecutionResult",
    "ExecutionSide",
    "ExecutionStatus",
]


class ExecutionStatus(str, Enum):
    """Identifies the structural outcomes available to future execution engines."""

    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    SKIPPED = "SKIPPED"


class ExecutionSide(str, Enum):
    """Identifies the explicit side of one already-completed trade."""

    LONG = "LONG"
    SHORT = "SHORT"


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


@dataclass(frozen=True, slots=True)
class CompletedTrade:
    """Records explicit immutable facts for one execution lifecycle already closed.

    An accepted execution result authorizes construction but does not itself imply
    completion. Side, quantity, entry price, and exit price are supplied facts.
    """

    source_execution_result: ExecutionResult
    side: ExecutionSide
    quantity: int
    entry_price: float
    exit_price: float

    def __post_init__(self) -> None:
        """Require explicit finite completed-trade facts without PnL inference."""
        if not isinstance(self.source_execution_result, ExecutionResult):
            raise TypeError("source_execution_result must be an ExecutionResult.")
        if self.source_execution_result.status is not ExecutionStatus.ACCEPTED:
            raise ValueError("source_execution_result must have ACCEPTED status.")
        if not isinstance(self.side, ExecutionSide):
            raise TypeError("side must be an ExecutionSide.")
        _validate_positive_quantity(self.quantity)
        _validate_finite_price(self.entry_price, "entry_price")
        _validate_finite_price(self.exit_price, "exit_price")


def _validate_positive_quantity(quantity: int) -> None:
    """Require an explicit positive integer quantity without accepting booleans."""
    if isinstance(quantity, bool) or not isinstance(quantity, int):
        raise TypeError("quantity must be an int.")
    if quantity <= 0:
        raise ValueError("quantity must be positive.")


def _validate_finite_price(price: float, field_name: str) -> None:
    """Require an explicit finite float price without accepting booleans."""
    if isinstance(price, bool) or not isinstance(price, float):
        raise TypeError(f"{field_name} must be a float.")
    if not isfinite(price):
        raise ValueError(f"{field_name} must be finite.")
