"""Immutable structural domain models for Performance Analytics."""

from dataclasses import dataclass
from enum import Enum

from src.engines.backtesting.models import BacktestRun

__all__ = ["PerformanceContext", "PerformanceReport", "PerformanceStatus"]


class PerformanceStatus(str, Enum):
    """Identifies the structural states available to future performance reports."""

    CREATED = "CREATED"
    ANALYZED = "ANALYZED"
    FAILED = "FAILED"


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


def _validate_count(value: int, field_name: str) -> None:
    """Require one non-negative integer count without accepting booleans."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an int.")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative.")
