"""Protocol boundary for future optimization summary report renderers."""

from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar

from src.engines.backtesting.summary import OptimizationRunSummaryReport

__all__ = [
    "OptimizationRunSummaryRenderedReport",
    "OptimizationRunSummaryReportRenderer",
    "MarkdownOptimizationRunSummaryReportRenderer",
    "PlainTextOptimizationRunSummaryReportRenderer",
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


@dataclass(frozen=True, slots=True)
class PlainTextOptimizationRunSummaryReportRenderer:
    """Render one summary report as deterministic plain text without analysis."""

    def render(
        self,
        report: OptimizationRunSummaryReport,
    ) -> OptimizationRunSummaryRenderedReport[str]:
        """Return fixed ordered plain text from retained aggregate and rate facts."""
        if not isinstance(report, OptimizationRunSummaryReport):
            raise TypeError("report must be an OptimizationRunSummaryReport.")
        aggregate = report.analysis.aggregate
        rates = report.analysis.rates
        payload = "\n".join(
            (
                "Optimization Run Summary",
                f"Run Count: {aggregate.run_count}",
                f"Evaluated Candidate Count: {aggregate.evaluated_candidate_count}",
                (
                    "Total Eligible Candidate Count: "
                    f"{aggregate.total_eligible_candidate_count}"
                ),
                f"Recorded Rejection Count: {aggregate.recorded_rejection_count}",
                (
                    "Search Space Exhausted Count: "
                    f"{aggregate.search_space_exhausted_count}"
                ),
                (
                    "Evaluation Budget Reached Count: "
                    f"{aggregate.evaluation_budget_reached_count}"
                ),
                f"Candidate Completion Rate: {rates.candidate_completion_rate}",
                f"Recorded Rejection Rate: {rates.recorded_rejection_rate}",
                (
                    "Search Space Exhausted Rate: "
                    f"{rates.search_space_exhausted_rate}"
                ),
                (
                    "Evaluation Budget Reached Rate: "
                    f"{rates.evaluation_budget_reached_rate}"
                ),
            )
        )
        return OptimizationRunSummaryRenderedReport(payload)


@dataclass(frozen=True, slots=True)
class MarkdownOptimizationRunSummaryReportRenderer:
    """Render one summary report as deterministic Markdown without analysis."""

    def render(
        self,
        report: OptimizationRunSummaryReport,
    ) -> OptimizationRunSummaryRenderedReport[str]:
        """Return a fixed ordered Markdown table from retained scalar facts."""
        if not isinstance(report, OptimizationRunSummaryReport):
            raise TypeError("report must be an OptimizationRunSummaryReport.")
        aggregate = report.analysis.aggregate
        rates = report.analysis.rates
        payload = "\n".join(
            (
                "# Optimization Run Summary",
                "",
                "| Metric | Value |",
                "| --- | --- |",
                f"| Run Count | {aggregate.run_count} |",
                (
                    "| Evaluated Candidate Count | "
                    f"{aggregate.evaluated_candidate_count} |"
                ),
                (
                    "| Total Eligible Candidate Count | "
                    f"{aggregate.total_eligible_candidate_count} |"
                ),
                (
                    "| Recorded Rejection Count | "
                    f"{aggregate.recorded_rejection_count} |"
                ),
                (
                    "| Search Space Exhausted Count | "
                    f"{aggregate.search_space_exhausted_count} |"
                ),
                (
                    "| Evaluation Budget Reached Count | "
                    f"{aggregate.evaluation_budget_reached_count} |"
                ),
                (
                    "| Candidate Completion Rate | "
                    f"{rates.candidate_completion_rate} |"
                ),
                (
                    "| Recorded Rejection Rate | "
                    f"{rates.recorded_rejection_rate} |"
                ),
                (
                    "| Search Space Exhausted Rate | "
                    f"{rates.search_space_exhausted_rate} |"
                ),
                (
                    "| Evaluation Budget Reached Rate | "
                    f"{rates.evaluation_budget_reached_rate} |"
                ),
            )
        )
        return OptimizationRunSummaryRenderedReport(payload)
