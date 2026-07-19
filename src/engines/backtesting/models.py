"""Immutable structural domain models for the Backtesting Engine."""

from dataclasses import dataclass
from enum import Enum

from src.engines.execution.interfaces import ExecutionEngine
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
    """References one immutable context and its structural lifecycle status."""

    context: BacktestContext
    status: BacktestStatus

    def __post_init__(self) -> None:
        """Require only the model types intrinsic to a structural run."""
        if not isinstance(self.context, BacktestContext):
            raise TypeError("context must be a BacktestContext.")
        if not isinstance(self.status, BacktestStatus):
            raise TypeError("status must be a BacktestStatus.")
