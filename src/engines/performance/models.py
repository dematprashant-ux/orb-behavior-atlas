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
    "PerformanceMetrics",
    "PerformanceReport",
    "PerformanceStatus",
    "EquityCurve",
    "EquityPoint",
    "DrawdownPoint",
    "DrawdownSummary",
    "RiskAdjustedMetrics",
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
class PerformanceMetrics:
    """Records deterministic non-portfolio metrics over realized trade PnL."""

    total_trades: int
    winning_trades: int
    losing_trades: int
    flat_trades: int
    gross_profit: float
    gross_loss: float
    net_profit: float
    win_rate: float
    loss_rate: float
    flat_rate: float
    average_trade_pnl: float
    average_winning_trade: float
    average_losing_trade: float
    profit_factor: float | None
    expectancy: float

    def __post_init__(self) -> None:
        """Require internally consistent counts and metrics without rounding."""
        counts = (
            (self.total_trades, "total_trades"),
            (self.winning_trades, "winning_trades"),
            (self.losing_trades, "losing_trades"),
            (self.flat_trades, "flat_trades"),
        )
        for count, field_name in counts:
            _validate_count(count, field_name)
        if (
            self.winning_trades + self.losing_trades + self.flat_trades
            != self.total_trades
        ):
            raise ValueError("trade counts must equal total_trades.")

        metrics = (
            (self.gross_profit, "gross_profit"),
            (self.gross_loss, "gross_loss"),
            (self.net_profit, "net_profit"),
            (self.win_rate, "win_rate"),
            (self.loss_rate, "loss_rate"),
            (self.flat_rate, "flat_rate"),
            (self.average_trade_pnl, "average_trade_pnl"),
            (self.average_winning_trade, "average_winning_trade"),
            (self.average_losing_trade, "average_losing_trade"),
            (self.expectancy, "expectancy"),
        )
        for value, field_name in metrics:
            _validate_finite_float(value, field_name)
        if self.gross_profit < 0 or self.gross_loss < 0:
            raise ValueError("gross_profit and gross_loss must be non-negative.")
        _validate_metric_relationships(self)


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
class EquityPoint:
    """Records one trade PnL item and its cumulative realized-equity value."""

    source_trade_pnl: TradePnL
    cumulative_realized_pnl: float

    def __post_init__(self) -> None:
        """Require one existing PnL item and a finite cumulative value."""
        if not isinstance(self.source_trade_pnl, TradePnL):
            raise TypeError("source_trade_pnl must be a TradePnL.")
        _validate_finite_float(self.cumulative_realized_pnl, "cumulative_realized_pnl")


@dataclass(frozen=True, slots=True)
class EquityCurve:
    """Records an ordered immutable realized-equity series and its final value."""

    equity_points: tuple[EquityPoint, ...]
    final_equity: float

    def __post_init__(self) -> None:
        """Require an immutable point collection with a consistent final value."""
        if not isinstance(self.equity_points, tuple):
            raise TypeError("equity_points must be a tuple of EquityPoint values.")
        if any(not isinstance(point, EquityPoint) for point in self.equity_points):
            raise TypeError("equity_points must contain only EquityPoint values.")
        _validate_finite_float(self.final_equity, "final_equity")
        expected_final_equity = (
            self.equity_points[-1].cumulative_realized_pnl
            if self.equity_points
            else 0.0
        )
        if self.final_equity != expected_final_equity:
            raise ValueError("final_equity must match the last cumulative value.")


@dataclass(frozen=True, slots=True)
class DrawdownPoint:
    """Records one equity point, its running peak, and absolute drawdown."""

    source_equity_point: EquityPoint
    running_peak: float
    drawdown: float

    def __post_init__(self) -> None:
        """Require finite non-negative drawdown facts consistent with the point."""
        if not isinstance(self.source_equity_point, EquityPoint):
            raise TypeError("source_equity_point must be an EquityPoint.")
        _validate_finite_float(self.running_peak, "running_peak")
        _validate_finite_float(self.drawdown, "drawdown")
        if self.running_peak < self.source_equity_point.cumulative_realized_pnl:
            raise ValueError("running_peak must not be below cumulative equity.")
        if self.drawdown < 0:
            raise ValueError("drawdown must be non-negative.")
        if self.drawdown != (
            self.running_peak - self.source_equity_point.cumulative_realized_pnl
        ):
            raise ValueError(
                "drawdown must match running peak minus cumulative equity."
            )


@dataclass(frozen=True, slots=True)
class DrawdownSummary:
    """Records ordered immutable drawdown points and maximum absolute drawdown."""

    drawdown_points: tuple[DrawdownPoint, ...]
    maximum_drawdown: float

    def __post_init__(self) -> None:
        """Require ordered point facts with a consistent maximum drawdown."""
        if not isinstance(self.drawdown_points, tuple):
            raise TypeError("drawdown_points must be a tuple of DrawdownPoint values.")
        if any(
            not isinstance(drawdown_point, DrawdownPoint)
            for drawdown_point in self.drawdown_points
        ):
            raise TypeError("drawdown_points must contain only DrawdownPoint values.")
        _validate_finite_float(self.maximum_drawdown, "maximum_drawdown")
        if self.maximum_drawdown < 0:
            raise ValueError("maximum_drawdown must be non-negative.")
        if any(
            current.running_peak < previous.running_peak
            for previous, current in zip(
                self.drawdown_points,
                self.drawdown_points[1:],
            )
        ):
            raise ValueError("running_peak must not decrease.")
        expected_maximum_drawdown = max(
            (point.drawdown for point in self.drawdown_points),
            default=0.0,
        )
        if self.maximum_drawdown != expected_maximum_drawdown:
            raise ValueError("maximum_drawdown must match supplied drawdown points.")


@dataclass(frozen=True, slots=True)
class RiskAdjustedMetrics:
    """Records zero-safe absolute-return-to-drawdown ratios."""

    recovery_factor: float | None
    return_over_drawdown: float | None

    def __post_init__(self) -> None:
        """Require finite, equivalent values for the identical documented ratios."""
        _validate_optional_finite_float(self.recovery_factor, "recovery_factor")
        _validate_optional_finite_float(
            self.return_over_drawdown,
            "return_over_drawdown",
        )
        if self.recovery_factor != self.return_over_drawdown:
            raise ValueError(
                "recovery_factor and return_over_drawdown must match."
            )


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


def _validate_optional_finite_float(value: float | None, field_name: str) -> None:
    """Allow an unavailable ratio or require one finite float value."""
    if value is not None:
        _validate_finite_float(value, field_name)


def _validate_metric_relationships(metrics: PerformanceMetrics) -> None:
    """Require metrics to follow the documented zero-safe aggregate formulas."""
    if metrics.total_trades == 0:
        expected_rates = (0.0, 0.0, 0.0)
        expected_averages = (0.0, 0.0, 0.0, 0.0)
    else:
        expected_rates = (
            metrics.winning_trades / metrics.total_trades,
            metrics.losing_trades / metrics.total_trades,
            metrics.flat_trades / metrics.total_trades,
        )
        expected_averages = (
            metrics.net_profit / metrics.total_trades,
            (
                metrics.gross_profit / metrics.winning_trades
                if metrics.winning_trades
                else 0.0
            ),
            (
                -metrics.gross_loss / metrics.losing_trades
                if metrics.losing_trades
                else 0.0
            ),
            metrics.net_profit / metrics.total_trades,
        )
    if (
        (metrics.win_rate, metrics.loss_rate, metrics.flat_rate) != expected_rates
        or (
            metrics.average_trade_pnl,
            metrics.average_winning_trade,
            metrics.average_losing_trade,
            metrics.expectancy,
        )
        != expected_averages
    ):
        raise ValueError("rates and averages must match the aggregate trade facts.")

    if metrics.profit_factor is not None:
        _validate_finite_float(metrics.profit_factor, "profit_factor")
    expected_profit_factor = (
        metrics.gross_profit / metrics.gross_loss if metrics.gross_loss else None
    )
    if metrics.profit_factor != expected_profit_factor:
        raise ValueError("profit_factor must match gross profit and gross loss.")


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
