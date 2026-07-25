"""Protocol boundary for future optimization summary report renderers."""

from typing import Protocol, TypeVar

from src.engines.backtesting.summary import OptimizationRunSummaryReport

__all__ = ["OptimizationRunSummaryReportRenderer"]


_RenderedOptimizationRunSummaryReport = TypeVar(
    "_RenderedOptimizationRunSummaryReport",
    covariant=True,
)


class OptimizationRunSummaryReportRenderer(
    Protocol[_RenderedOptimizationRunSummaryReport],
):
    """Define renderer-independent presentation of one summary report."""

    def render(
        self,
        report: OptimizationRunSummaryReport,
    ) -> _RenderedOptimizationRunSummaryReport:
        """Return one future rendered value without defining its representation."""
