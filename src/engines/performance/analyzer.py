"""Deterministic summary counting over existing backtest execution results."""

from src.engines.backtesting.models import BacktestStatus
from src.engines.execution.models import ExecutionStatus
from src.engines.performance.builders import build_performance_report
from src.engines.performance.models import (
    PerformanceContext,
    PerformanceReport,
    PerformanceStatus,
)

__all__ = ["BasicPerformanceEngine"]


class BasicPerformanceEngine:
    """Produce immutable execution-status counts from one completed backtest run.

    This analyzer only counts existing structural execution outcomes. It does not
    inspect market data, execute requests, calculate financial metrics, mutate
    inputs, or perform I/O.
    """

    def analyze(self, context: PerformanceContext) -> PerformanceReport:
        """Return deterministic accepted, rejected, and skipped-result counts.

        Args:
            context: Existing immutable context holding a completed backtest run.

        Returns:
            An analyzed immutable report with execution-status counts only.

        Raises:
            TypeError: If ``context`` is not a ``PerformanceContext``.
            ValueError: If the context does not reference a completed backtest run.
        """
        if not isinstance(context, PerformanceContext):
            raise TypeError("context must be a PerformanceContext.")
        if context.backtest_run.status is not BacktestStatus.COMPLETED:
            raise ValueError("backtest_run must have COMPLETED status.")

        accepted_count = 0
        rejected_count = 0
        skipped_count = 0
        for execution_result in context.backtest_run.execution_results:
            if execution_result.status is ExecutionStatus.ACCEPTED:
                accepted_count += 1
            elif execution_result.status is ExecutionStatus.REJECTED:
                rejected_count += 1
            elif execution_result.status is ExecutionStatus.SKIPPED:
                skipped_count += 1

        return build_performance_report(
            context=context,
            status=PerformanceStatus.ANALYZED,
            total_execution_results=len(context.backtest_run.execution_results),
            accepted_count=accepted_count,
            rejected_count=rejected_count,
            skipped_count=skipped_count,
        )
