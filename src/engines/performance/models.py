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
    """References one analysis context and its structural lifecycle status."""

    context: PerformanceContext
    status: PerformanceStatus

    def __post_init__(self) -> None:
        """Require only the model types intrinsic to a structural report."""
        if not isinstance(self.context, PerformanceContext):
            raise TypeError("context must be a PerformanceContext.")
        if not isinstance(self.status, PerformanceStatus):
            raise TypeError("status must be a PerformanceStatus.")
