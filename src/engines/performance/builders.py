"""Pure construction of immutable Performance Analytics contexts and reports."""

from src.engines.backtesting.models import BacktestRun
from src.engines.execution.models import CompletedTrade
from src.engines.performance.models import (
    DrawdownPoint,
    DrawdownSummary,
    EquityCurve,
    EquityPoint,
    PerformanceContext,
    PerformanceMetrics,
    PerformanceReport,
    PerformanceStatus,
    PnLSummary,
    RiskAdjustedMetrics,
    TradePnL,
)

__all__ = [
    "build_performance_context",
    "build_performance_metrics",
    "build_performance_report",
    "build_equity_curve",
    "build_equity_point",
    "build_drawdown_point",
    "build_drawdown_summary",
    "build_risk_adjusted_metrics",
    "build_pnl_summary",
    "build_trade_pnl",
]


def build_performance_context(backtest_run: BacktestRun) -> PerformanceContext:
    """Build a context retaining one existing backtest-run reference.

    The builder performs no performance calculation, report generation, or I/O.

    Args:
        backtest_run: Existing immutable backtest run for future analysis.

    Returns:
        An immutable context retaining ``backtest_run`` by reference.

    Raises:
        TypeError: If ``backtest_run`` is not a ``BacktestRun``.
    """
    if not isinstance(backtest_run, BacktestRun):
        raise TypeError("backtest_run must be a BacktestRun.")
    return PerformanceContext(backtest_run=backtest_run)


def build_performance_report(
    context: PerformanceContext,
    status: PerformanceStatus,
    total_execution_results: int = 0,
    accepted_count: int = 0,
    rejected_count: int = 0,
    skipped_count: int = 0,
) -> PerformanceReport:
    """Build a report retaining one context, status, and execution-status counts.

    Args:
        context: Existing immutable performance-analysis context.
        status: Structural lifecycle status for the report.
        total_execution_results: Number of existing execution results observed.
        accepted_count: Number of results with accepted status.
        rejected_count: Number of results with rejected status.
        skipped_count: Number of results with skipped status.

    Returns:
        An immutable report retaining ``context`` by reference.

    Raises:
        TypeError: If either input has an unsupported model type.
    """
    if not isinstance(context, PerformanceContext):
        raise TypeError("context must be a PerformanceContext.")
    if not isinstance(status, PerformanceStatus):
        raise TypeError("status must be a PerformanceStatus.")
    return PerformanceReport(
        context=context,
        status=status,
        total_execution_results=total_execution_results,
        accepted_count=accepted_count,
        rejected_count=rejected_count,
        skipped_count=skipped_count,
    )


def build_trade_pnl(
    source_completed_trade: CompletedTrade,
    realized_pnl: float,
) -> TradePnL:
    """Build one realized-PnL item from an existing completed trade and value.

    Args:
        source_completed_trade: Existing immutable explicit completed trade.
        realized_pnl: Finite PnL value derived only from the completed trade facts.

    Returns:
        An immutable item retaining ``source_completed_trade`` by reference.

    Raises:
        TypeError: If an input has an unsupported type.
        ValueError: If the PnL is non-finite or inconsistent with the trade.
    """
    return TradePnL(
        source_completed_trade=source_completed_trade,
        realized_pnl=realized_pnl,
    )


def build_pnl_summary(
    trade_pnls: tuple[TradePnL, ...],
    total_realized_pnl: float | None = None,
) -> PnLSummary:
    """Build an immutable ordered realized-PnL summary.

    When no total is supplied, the builder sums existing PnL items using native
    float arithmetic and applies no rounding.

    Args:
        trade_pnls: Ordered immutable realized-PnL items.
        total_realized_pnl: Optional explicit total to validate against the items.

    Returns:
        An immutable summary retaining the supplied PnL item references.

    Raises:
        TypeError: If an input has an unsupported type.
        ValueError: If an explicit total is invalid or inconsistent.
    """
    if not isinstance(trade_pnls, tuple):
        raise TypeError("trade_pnls must be a tuple of TradePnL values.")
    if any(not isinstance(trade_pnl, TradePnL) for trade_pnl in trade_pnls):
        raise TypeError("trade_pnls must contain only TradePnL values.")
    if total_realized_pnl is None:
        total_realized_pnl = sum(
            (trade_pnl.realized_pnl for trade_pnl in trade_pnls),
            start=0.0,
        )
    return PnLSummary(
        trade_pnls=trade_pnls,
        total_realized_pnl=total_realized_pnl,
    )


def build_performance_metrics(
    total_trades: int,
    winning_trades: int,
    losing_trades: int,
    flat_trades: int,
    gross_profit: float,
    gross_loss: float,
    net_profit: float,
    win_rate: float,
    loss_rate: float,
    flat_rate: float,
    average_trade_pnl: float,
    average_winning_trade: float,
    average_losing_trade: float,
    profit_factor: float | None,
    expectancy: float,
) -> PerformanceMetrics:
    """Build immutable metrics after enforcing their aggregate invariants.

    The builder calculates no additional metrics and applies no rounding.
    """
    return PerformanceMetrics(
        total_trades=total_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        flat_trades=flat_trades,
        gross_profit=gross_profit,
        gross_loss=gross_loss,
        net_profit=net_profit,
        win_rate=win_rate,
        loss_rate=loss_rate,
        flat_rate=flat_rate,
        average_trade_pnl=average_trade_pnl,
        average_winning_trade=average_winning_trade,
        average_losing_trade=average_losing_trade,
        profit_factor=profit_factor,
        expectancy=expectancy,
    )


def build_equity_point(
    source_trade_pnl: TradePnL,
    cumulative_realized_pnl: float,
) -> EquityPoint:
    """Build one immutable cumulative realized-equity point.

    The builder retains the source PnL item by reference and performs no
    drawdown, rolling-statistic, or portfolio analysis.
    """
    return EquityPoint(
        source_trade_pnl=source_trade_pnl,
        cumulative_realized_pnl=cumulative_realized_pnl,
    )


def build_equity_curve(
    equity_points: tuple[EquityPoint, ...],
    final_equity: float | None = None,
) -> EquityCurve:
    """Build an immutable ordered cumulative-realized-equity curve.

    When omitted, ``final_equity`` retains the last supplied cumulative point or
    zero for an empty curve. No additional financial calculation is performed.
    """
    if not isinstance(equity_points, tuple):
        raise TypeError("equity_points must be a tuple of EquityPoint values.")
    if any(not isinstance(point, EquityPoint) for point in equity_points):
        raise TypeError("equity_points must contain only EquityPoint values.")
    if final_equity is None:
        final_equity = (
            equity_points[-1].cumulative_realized_pnl if equity_points else 0.0
        )
    return EquityCurve(equity_points=equity_points, final_equity=final_equity)


def build_drawdown_point(
    source_equity_point: EquityPoint,
    running_peak: float,
    drawdown: float,
) -> DrawdownPoint:
    """Build one immutable absolute-drawdown point from existing equity facts."""
    return DrawdownPoint(
        source_equity_point=source_equity_point,
        running_peak=running_peak,
        drawdown=drawdown,
    )


def build_drawdown_summary(
    drawdown_points: tuple[DrawdownPoint, ...],
    maximum_drawdown: float | None = None,
) -> DrawdownSummary:
    """Build an immutable ordered absolute-drawdown summary.

    An omitted maximum retains the largest supplied drawdown, or zero for an
    empty summary. No percentage or risk-adjusted metric is calculated.
    """
    if not isinstance(drawdown_points, tuple):
        raise TypeError("drawdown_points must be a tuple of DrawdownPoint values.")
    if any(
        not isinstance(drawdown_point, DrawdownPoint)
        for drawdown_point in drawdown_points
    ):
        raise TypeError("drawdown_points must contain only DrawdownPoint values.")
    if maximum_drawdown is None:
        maximum_drawdown = max(
            (point.drawdown for point in drawdown_points),
            default=0.0,
        )
    return DrawdownSummary(
        drawdown_points=drawdown_points,
        maximum_drawdown=maximum_drawdown,
    )


def build_risk_adjusted_metrics(
    recovery_factor: float | None,
    return_over_drawdown: float | None,
) -> RiskAdjustedMetrics:
    """Build zero-safe absolute-return-to-drawdown metric values.

    Both documented metric names use the same formula in this milestone. The
    model therefore requires their values to match and applies no rounding.
    """
    return RiskAdjustedMetrics(
        recovery_factor=recovery_factor,
        return_over_drawdown=return_over_drawdown,
    )
