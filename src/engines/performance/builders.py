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
