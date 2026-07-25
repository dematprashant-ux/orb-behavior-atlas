"""Protocol boundary for future optimization summary report renderers."""

from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar

from src.engines.backtesting.summary import OptimizationRunSummaryReport

__all__ = [
    "OptimizationRunSummaryRenderedReport",
    "OptimizationRunSummaryReportRenderer",
]


_RenderedOptimizationRunSummaryPayload = TypeVar(
    "_RenderedOptimizationRunSummaryPayload",
    covariant=True,
)


@dataclass(frozen=True, slots=True)
class OptimizationRunSummaryRenderedReport(
    Generic[_RenderedOptimizationRunSummaryPayload],
):
    """Retain one renderer-defined payload without defining its representation."""

    payload: _RenderedOptimizationRunSummaryPayload

    def __post_init__(self) -> None:
        """Require one explicit payload while preserving its exact identity."""
        if self.payload is None:
            raise TypeError("payload must not be None.")


class OptimizationRunSummaryReportRenderer(
    Protocol[_RenderedOptimizationRunSummaryPayload],
):
    """Define renderer-independent presentation of one summary report."""

    def render(
        self,
        report: OptimizationRunSummaryReport,
    ) -> OptimizationRunSummaryRenderedReport[
        _RenderedOptimizationRunSummaryPayload
    ]:
        """Return one future rendered value without defining its representation."""
