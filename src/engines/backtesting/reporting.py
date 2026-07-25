"""Protocol boundary for future optimization summary report renderers."""

from dataclasses import dataclass
from html import escape
from typing import Generic, Protocol, TypeVar

from src.engines.backtesting.ranking import RankedObjectiveScore
from src.engines.backtesting.summary import (
    OptimizationResultReport,
    OptimizationSelectionOutcomeReport,
    OptimizationRunSummaries,
    OptimizationRunSummary,
    OptimizationRunSummaryAnalysis,
    OptimizationRunSummaryReport,
)

__all__ = [
    "OptimizationResultRenderedReport",
    "OptimizationResultReportRenderer",
    "OptimizationResultReportingPipeline",
    "OptimizationSelectionOutcomeReportRenderer",
    "OptimizationSelectionOutcomeReportingPipeline",
    "MarkdownOptimizationSelectionOutcomeRenderer",
    "OptimizationRunSummaryRenderedReport",
    "OptimizationRunSummaryReportRenderer",
    "OptimizationRunSummaryReportingPipeline",
    "HtmlOptimizationRunSummaryReportRenderer",
    "MarkdownOptimizationRunSummaryReportRenderer",
    "PlainTextOptimizationRunSummaryReportRenderer",
]


_RenderedOptimizationRunSummaryPayload = TypeVar(
    "_RenderedOptimizationRunSummaryPayload",
    covariant=True,
)

_RenderedOptimizationResultPayload = TypeVar(
    "_RenderedOptimizationResultPayload",
    covariant=True,
)


@dataclass(frozen=True, slots=True)
class OptimizationResultRenderedReport(Generic[_RenderedOptimizationResultPayload]):
    """Retain one result-renderer payload without defining its representation."""

    payload: _RenderedOptimizationResultPayload

    def __post_init__(self) -> None:
        """Require one explicit payload while preserving its exact identity."""
        if self.payload is None:
            raise TypeError("payload must not be None.")


class OptimizationResultReportRenderer(Protocol[_RenderedOptimizationResultPayload]):
    """Define renderer-independent presentation of one optimization result."""

    def render(
        self,
        report: OptimizationResultReport,
    ) -> OptimizationResultRenderedReport[_RenderedOptimizationResultPayload]:
        """Return one renderer-defined result value without inspecting it."""


@dataclass(frozen=True, slots=True)
class OptimizationResultReportingPipeline(Generic[_RenderedOptimizationResultPayload]):
    """Delegate one completed result report through one injected renderer."""

    renderer: OptimizationResultReportRenderer[_RenderedOptimizationResultPayload]

    def __post_init__(self) -> None:
        """Require one explicit result renderer without invoking it."""
        if self.renderer is None:
            raise TypeError("renderer must not be None.")
        if not callable(getattr(self.renderer, "render", None)):
            raise TypeError("renderer must define a callable render method.")

    def render_report(
        self,
        report: OptimizationResultReport,
    ) -> OptimizationResultRenderedReport[_RenderedOptimizationResultPayload]:
        """Return the injected renderer's exact output for one existing report."""
        if not isinstance(report, OptimizationResultReport):
            raise TypeError("report must be an OptimizationResultReport.")
        return self.renderer.render(report)


class OptimizationSelectionOutcomeReportRenderer(
    Protocol[_RenderedOptimizationResultPayload],
):
    """Define presentation of complete canonical optimization selection outcomes."""

    def render(
        self,
        report: OptimizationSelectionOutcomeReport,
    ) -> OptimizationResultRenderedReport[_RenderedOptimizationResultPayload]:
        """Return one renderer-defined value without changing the outcome."""


@dataclass(frozen=True, slots=True)
class OptimizationSelectionOutcomeReportingPipeline(
    Generic[_RenderedOptimizationResultPayload],
):
    """Compose one canonical selection outcome through an injected renderer."""

    renderer: OptimizationSelectionOutcomeReportRenderer[
        _RenderedOptimizationResultPayload
    ]

    def __post_init__(self) -> None:
        """Require one explicit outcome renderer without invoking it."""
        if self.renderer is None:
            raise TypeError("renderer must not be None.")
        if not callable(getattr(self.renderer, "render", None)):
            raise TypeError("renderer must define a callable render method.")

    def render_report(
        self,
        result_report: OptimizationResultReport,
    ) -> OptimizationResultRenderedReport[_RenderedOptimizationResultPayload]:
        """Render one canonical outcome without reranking or reselection."""
        if not isinstance(result_report, OptimizationResultReport):
            raise TypeError("result_report must be an OptimizationResultReport.")
        outcome_report = OptimizationSelectionOutcomeReport.from_result_report(
            result_report
        )
        return self.renderer.render(outcome_report)


@dataclass(frozen=True, slots=True)
class MarkdownOptimizationSelectionOutcomeRenderer:
    """Render complete selected outcomes as deterministic Markdown tables."""

    def render(
        self,
        report: OptimizationSelectionOutcomeReport,
    ) -> OptimizationResultRenderedReport[str]:
        """Return canonical selected facts without reranking or tie breaking."""
        if not isinstance(report, OptimizationSelectionOutcomeReport):
            raise TypeError("report must be an OptimizationSelectionOutcomeReport.")
        rows = tuple(
            _render_selected_outcome_row(selected_outcome)
            for selected_outcome in report.selected_outcomes
        )
        return OptimizationResultRenderedReport(
            "\n".join(
                (
                    "# Optimization Selection Outcome",
                    "",
                    "## Summary",
                    "",
                    f"Selection Count: {report.selection_count}",
                    "",
                    "## Selected Outcomes",
                    "",
                    "| Rank | Parameters | Objective Score | Direction |",
                    "| --- | --- | --- | --- |",
                    *rows,
                )
            )
        )


def _render_selected_outcome_row(selected_outcome: RankedObjectiveScore) -> str:
    """Render one existing selected outcome without calculating a new value."""
    source_score = selected_outcome.source_score
    parameters = "; ".join(
        f"{_escape_markdown_cell(name)}={_escape_markdown_cell(value)}"
        for name, value in source_score.evaluation.candidate.assignments
    )
    return (
        "| "
        f"{selected_outcome.rank} | {parameters} | {source_score.score} | "
        f"{source_score.direction.value} |"
    )


def _escape_markdown_cell(value: object) -> str:
    """Keep canonical text in one deterministic Markdown table cell."""
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\n", "\\n")
        .replace("|", "\\|")
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
class OptimizationRunSummaryReportingPipeline(
    Generic[_RenderedOptimizationRunSummaryPayload],
):
    """Compose canonical one-run reporting stages through one injected renderer."""

    renderer: OptimizationRunSummaryReportRenderer[
        _RenderedOptimizationRunSummaryPayload
    ]

    def __post_init__(self) -> None:
        """Require one explicit renderer contract without invoking it."""
        if self.renderer is None:
            raise TypeError("renderer must not be None.")
        if not callable(getattr(self.renderer, "render", None)):
            raise TypeError("renderer must define a callable render method.")

    def render_run(
        self,
        run: "OptimizationRun",
    ) -> OptimizationRunSummaryRenderedReport[
        _RenderedOptimizationRunSummaryPayload
    ]:
        """Render one completed run through canonical summary composition only."""
        from src.engines.backtesting.optimization import OptimizationRun

        if not isinstance(run, OptimizationRun):
            raise TypeError("run must be an OptimizationRun.")
        summary = OptimizationRunSummary.from_run(run)
        summaries = OptimizationRunSummaries((summary,))
        analysis = OptimizationRunSummaryAnalysis.from_summaries(summaries)
        report = OptimizationRunSummaryReport.from_analysis(analysis)
        return self.renderer.render(report)


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


@dataclass(frozen=True, slots=True)
class HtmlOptimizationRunSummaryReportRenderer:
    """Render one summary report as a deterministic semantic HTML fragment."""

    def render(
        self,
        report: OptimizationRunSummaryReport,
    ) -> OptimizationRunSummaryRenderedReport[str]:
        """Return a fixed HTML section from retained aggregate and rate facts."""
        if not isinstance(report, OptimizationRunSummaryReport):
            raise TypeError("report must be an OptimizationRunSummaryReport.")
        aggregate = report.analysis.aggregate
        rates = report.analysis.rates
        metric_values = (
            ("Run Count", aggregate.run_count),
            ("Evaluated Candidate Count", aggregate.evaluated_candidate_count),
            (
                "Total Eligible Candidate Count",
                aggregate.total_eligible_candidate_count,
            ),
            ("Recorded Rejection Count", aggregate.recorded_rejection_count),
            (
                "Search Space Exhausted Count",
                aggregate.search_space_exhausted_count,
            ),
            (
                "Evaluation Budget Reached Count",
                aggregate.evaluation_budget_reached_count,
            ),
            ("Candidate Completion Rate", rates.candidate_completion_rate),
            ("Recorded Rejection Rate", rates.recorded_rejection_rate),
            ("Search Space Exhausted Rate", rates.search_space_exhausted_rate),
            (
                "Evaluation Budget Reached Rate",
                rates.evaluation_budget_reached_rate,
            ),
        )
        lines = [
            "<section>",
            "<h1>Optimization Run Summary</h1>",
            "<table>",
            "<thead>",
            "<tr>",
            "<th>Metric</th>",
            "<th>Value</th>",
            "</tr>",
            "</thead>",
            "<tbody>",
        ]
        for metric, value in metric_values:
            lines.extend(
                (
                    "<tr>",
                    f"<td>{metric}</td>",
                    f"<td>{escape(str(value), quote=True)}</td>",
                    "</tr>",
                )
            )
        lines.extend(("</tbody>", "</table>", "</section>"))
        return OptimizationRunSummaryRenderedReport("\n".join(lines))
