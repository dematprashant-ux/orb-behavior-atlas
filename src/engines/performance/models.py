"""Immutable structural domain models for Performance Analytics."""

from dataclasses import dataclass
from enum import Enum

from src.engines.backtesting.models import BacktestRun
from src.engines.execution.models import ExecutionResult, ExecutionStatus

__all__ = [
    "PerformanceContext",
    "PerformanceReport",
    "PerformanceStatus",
    "TradeOutcome",
    "TradeOutcomeType",
]


class PerformanceStatus(str, Enum):
    """Identifies the structural states available to future performance reports."""

    CREATED = "CREATED"
    ANALYZED = "ANALYZED"
    FAILED = "FAILED"


class TradeOutcomeType(str, Enum):
    """Identifies the non-financial result of one execution outcome."""

    EXECUTED = "EXECUTED"
    REJECTED = "REJECTED"
    SKIPPED = "SKIPPED"


@dataclass(frozen=True, slots=True)
class PerformanceContext:
    """References one existing immutable backtest run for future analysis."""

    backtest_run: BacktestRun

    def __post_init__(self) -> None:
        """Require the existing backtest-run model intrinsic to this context."""
        if not isinstance(self.backtest_run, BacktestRun):
            raise TypeError("backtest_run must be a BacktestRun.")


@dataclass(frozen=True, slots=True)
class PerformanceReport:
    """References an analysis context, status, and immutable execution counts."""

    context: PerformanceContext
    status: PerformanceStatus
    total_execution_results: int = 0
    accepted_count: int = 0
    rejected_count: int = 0
    skipped_count: int = 0

    def __post_init__(self) -> None:
        """Require only the model types intrinsic to a structural report."""
        if not isinstance(self.context, PerformanceContext):
            raise TypeError("context must be a PerformanceContext.")
        if not isinstance(self.status, PerformanceStatus):
            raise TypeError("status must be a PerformanceStatus.")
        _validate_count(self.total_execution_results, "total_execution_results")
        _validate_count(self.accepted_count, "accepted_count")
        _validate_count(self.rejected_count, "rejected_count")
        _validate_count(self.skipped_count, "skipped_count")
        if (
            self.accepted_count + self.rejected_count + self.skipped_count
            != self.total_execution_results
        ):
            raise ValueError(
                "execution-status counts must equal total_execution_results."
            )


@dataclass(frozen=True, slots=True)
class TradeOutcome:
    """Classifies one existing execution result without duplicating its state."""

    execution_result: ExecutionResult
    outcome_type: TradeOutcomeType

    def __post_init__(self) -> None:
        """Require only the immutable execution result and outcome model types."""
        if not isinstance(self.execution_result, ExecutionResult):
            raise TypeError("execution_result must be an ExecutionResult.")
        if not isinstance(self.outcome_type, TradeOutcomeType):
            raise TypeError("outcome_type must be a TradeOutcomeType.")
        if self.outcome_type is not _outcome_type_for(self.execution_result.status):
            raise ValueError("outcome_type must match the execution result status.")


def _validate_count(value: int, field_name: str) -> None:
    """Require one non-negative integer count without accepting booleans."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an int.")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative.")


def _outcome_type_for(execution_status: ExecutionStatus) -> TradeOutcomeType:
    """Map one existing execution status to its immutable outcome type."""
    if execution_status is ExecutionStatus.ACCEPTED:
        return TradeOutcomeType.EXECUTED
    if execution_status is ExecutionStatus.REJECTED:
        return TradeOutcomeType.REJECTED
    return TradeOutcomeType.SKIPPED
