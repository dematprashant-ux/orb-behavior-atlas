"""Immutable structural domain models for the Backtesting Engine."""

from dataclasses import dataclass
from enum import Enum

from src.engines.execution.interfaces import ExecutionEngine
from src.engines.execution.models import ExecutionResult
from src.engines.research.orb.models import ORBBehaviorAtlas
from src.engines.strategy.interfaces import Strategy

__all__ = ["BacktestContext", "BacktestRun", "BacktestStatus"]


class BacktestStatus(str, Enum):
    """Identifies the structural lifecycle states available to future runs."""

    CREATED = "CREATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class BacktestContext:
    """References historical research artifacts and injected strategy services."""

    behavior_atlas: ORBBehaviorAtlas
    strategy: Strategy
    execution_engine: ExecutionEngine


@dataclass(frozen=True, slots=True)
class BacktestRun:
    """References one immutable context, status, and delegated execution results."""

    context: BacktestContext
    status: BacktestStatus
    execution_results: tuple[ExecutionResult, ...] = ()

    def __post_init__(self) -> None:
        """Require only the model types intrinsic to a structural run."""
        if not isinstance(self.context, BacktestContext):
            raise TypeError("context must be a BacktestContext.")
        if not isinstance(self.status, BacktestStatus):
            raise TypeError("status must be a BacktestStatus.")
        if not isinstance(self.execution_results, tuple):
            raise TypeError(
                "execution_results must be a tuple of ExecutionResult values."
            )
        if any(
            not isinstance(execution_result, ExecutionResult)
            for execution_result in self.execution_results
        ):
            raise TypeError(
                "execution_results must contain only ExecutionResult values."
            )
