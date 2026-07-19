"""Pure construction of immutable Performance Analytics contexts and reports."""

from src.engines.backtesting.models import BacktestRun
from src.engines.performance.models import (
    PerformanceContext,
    PerformanceReport,
    PerformanceStatus,
)

__all__ = ["build_performance_context", "build_performance_report"]


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
) -> PerformanceReport:
    """Build a report retaining one context reference and a structural status.

    Args:
        context: Existing immutable performance-analysis context.
        status: Structural lifecycle status for the report.

    Returns:
        An immutable report retaining ``context`` by reference.

    Raises:
        TypeError: If either input has an unsupported model type.
    """
    if not isinstance(context, PerformanceContext):
        raise TypeError("context must be a PerformanceContext.")
    if not isinstance(status, PerformanceStatus):
        raise TypeError("status must be a PerformanceStatus.")
    return PerformanceReport(context=context, status=status)
