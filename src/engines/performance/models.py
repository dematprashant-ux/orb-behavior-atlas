"""Immutable structural domain models for Performance Analytics."""

from dataclasses import dataclass
from enum import Enum
from math import isfinite

from src.engines.backtesting.models import BacktestRun
from src.engines.execution.models import (
    CompletedTrade,
    ExecutionResult,
    ExecutionSide,
    ExecutionStatus,
)

__all__ = [
    "PerformanceContext",
    "PerformanceReport",
    "PerformanceStatus",
    "PnLSummary",
    "TradePnL",
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
class TradePnL:
    """Records the realized PnL from one explicit immutable completed trade."""

    source_completed_trade: CompletedTrade
    realized_pnl: float

    def __post_init__(self) -> None:
        """Require a finite PnL value consistent with supplied trade facts."""
        if not isinstance(self.source_completed_trade, CompletedTrade):
            raise TypeError("source_completed_trade must be a CompletedTrade.")
        _validate_finite_float(self.realized_pnl, "realized_pnl")
        if self.realized_pnl != _calculate_realized_pnl(self.source_completed_trade):
            raise ValueError("realized_pnl must match the completed trade facts.")


@dataclass(frozen=True, slots=True)
class PnLSummary:
    """Records ordered immutable realized-PnL items and their exact total."""

    trade_pnls: tuple[TradePnL, ...]
    total_realized_pnl: float

    def __post_init__(self) -> None:
        """Require finite totals consistent with the supplied immutable items."""
        if not isinstance(self.trade_pnls, tuple):
            raise TypeError("trade_pnls must be a tuple of TradePnL values.")
        if any(not isinstance(trade_pnl, TradePnL) for trade_pnl in self.trade_pnls):
            raise TypeError("trade_pnls must contain only TradePnL values.")
        _validate_finite_float(self.total_realized_pnl, "total_realized_pnl")
        if self.total_realized_pnl != sum(
            (trade_pnl.realized_pnl for trade_pnl in self.trade_pnls),
            start=0.0,
        ):
            raise ValueError("total_realized_pnl must equal the supplied trade PnLs.")


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


def _validate_finite_float(value: float, field_name: str) -> None:
    """Require one finite float without accepting booleans or integer substitutes."""
    if isinstance(value, bool) or not isinstance(value, float):
        raise TypeError(f"{field_name} must be a float.")
    if not isfinite(value):
        raise ValueError(f"{field_name} must be finite.")


def _calculate_realized_pnl(completed_trade: CompletedTrade) -> float:
    """Calculate realized PnL from explicit completed-trade facts only."""
    price_difference = completed_trade.exit_price - completed_trade.entry_price
    if completed_trade.side is ExecutionSide.SHORT:
        price_difference = -price_difference
    return price_difference * completed_trade.quantity


def _outcome_type_for(execution_status: ExecutionStatus) -> TradeOutcomeType:
    """Map one existing execution status to its immutable outcome type."""
    if execution_status is ExecutionStatus.ACCEPTED:
        return TradeOutcomeType.EXECUTED
    if execution_status is ExecutionStatus.REJECTED:
        return TradeOutcomeType.REJECTED
    return TradeOutcomeType.SKIPPED
