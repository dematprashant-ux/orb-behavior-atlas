"""Protocol boundary for future optimization summary report renderers."""

from dataclasses import dataclass
from enum import Enum
from html import escape
from typing import Generic, Protocol, TypeVar

from src.engines.backtesting.optimization import OptimizationRunner
from src.engines.backtesting.ranking import RankedObjectiveScore
from src.engines.backtesting.selection import ObjectiveSelection, SelectionPolicy
from src.engines.backtesting.specification import OptimizationSpecification
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
    "OptimizationSelectionOutcomeReportingWorkflow",
    "OptimizationSelectionOutcomeReportingService",
    "OptimizationReportingFacade",
    "OptimizationReportFormat",
    "OptimizationReportingRouter",
    "OptimizationReportingCompositionRoot",
    "OptimizationExecutionReportingWorkflow",
    "OptimizationExecutionReportingCompositionRoot",
    "MarkdownOptimizationSelectionOutcomeRenderer",
    "PlainTextOptimizationSelectionOutcomeRenderer",
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


class OptimizationReportFormat(str, Enum):
    """Identify completed optimization selection-outcome presentation formats."""

    PLAIN_TEXT = "plain_text"
    MARKDOWN = "markdown"


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
class OptimizationSelectionOutcomeReportingWorkflow(
    Generic[_RenderedOptimizationResultPayload],
):
    """Connect completed optimization artifacts to outcome reporting once."""

    reporting_pipeline: OptimizationSelectionOutcomeReportingPipeline[
        _RenderedOptimizationResultPayload
    ]

    def __post_init__(self) -> None:
        """Require one injected reporting pipeline without invoking it."""
        if self.reporting_pipeline is None:
            raise TypeError("reporting_pipeline must not be None.")
        if not callable(getattr(self.reporting_pipeline, "render_report", None)):
            raise TypeError(
                "reporting_pipeline must define a callable render_report method."
            )

    def run(
        self,
        optimization_run: "OptimizationRun",
        selection: "ObjectiveSelection",
    ) -> OptimizationResultRenderedReport[_RenderedOptimizationResultPayload]:
        """Create one canonical result report and delegate it unchanged."""
        from src.engines.backtesting.optimization import OptimizationRun
        from src.engines.backtesting.selection import ObjectiveSelection

        if not isinstance(optimization_run, OptimizationRun):
            raise TypeError("optimization_run must be an OptimizationRun.")
        if not isinstance(selection, ObjectiveSelection):
            raise TypeError("selection must be an ObjectiveSelection.")
        result_report = OptimizationResultReport.from_run_and_selection(
            optimization_run,
            selection,
        )
        return self.reporting_pipeline.render_report(result_report)


@dataclass(frozen=True, slots=True)
class OptimizationSelectionOutcomeReportingService(
    Generic[_RenderedOptimizationResultPayload],
):
    """Select once from one completed run before delegating outcome reporting."""

    selection_policy: SelectionPolicy
    reporting_workflow: OptimizationSelectionOutcomeReportingWorkflow[
        _RenderedOptimizationResultPayload
    ]

    def __post_init__(self) -> None:
        """Require explicit selection and reporting collaborators only."""
        if self.selection_policy is None:
            raise TypeError("selection_policy must not be None.")
        if not callable(getattr(self.selection_policy, "select", None)):
            raise TypeError("selection_policy must define a callable select method.")
        if self.reporting_workflow is None:
            raise TypeError("reporting_workflow must not be None.")
        if not callable(getattr(self.reporting_workflow, "run", None)):
            raise TypeError("reporting_workflow must define a callable run method.")

    def run(
        self,
        optimization_run: "OptimizationRun",
    ) -> OptimizationResultRenderedReport[_RenderedOptimizationResultPayload]:
        """Select once from the exact run ranking and delegate unchanged."""
        from src.engines.backtesting.optimization import OptimizationRun

        if not isinstance(optimization_run, OptimizationRun):
            raise TypeError("optimization_run must be an OptimizationRun.")
        selection = self.selection_policy.select(optimization_run.ranking)
        if not isinstance(selection, ObjectiveSelection):
            raise TypeError(
                "selection_policy.select must return an ObjectiveSelection."
            )
        return self.reporting_workflow.run(optimization_run, selection)


@dataclass(frozen=True, slots=True)
class OptimizationReportingFacade(Generic[_RenderedOptimizationResultPayload]):
    """Expose one application entry point over injected outcome reporting."""

    reporting_service: OptimizationSelectionOutcomeReportingService[
        _RenderedOptimizationResultPayload
    ]

    def __post_init__(self) -> None:
        """Require one injected reporting service without invoking it."""
        if self.reporting_service is None:
            raise TypeError("reporting_service must not be None.")
        if not callable(getattr(self.reporting_service, "run", None)):
            raise TypeError("reporting_service must define a callable run method.")

    def render_run(
        self,
        optimization_run: "OptimizationRun",
    ) -> OptimizationResultRenderedReport[_RenderedOptimizationResultPayload]:
        """Delegate one exact completed run to the reporting service once."""
        from src.engines.backtesting.optimization import OptimizationRun

        if not isinstance(optimization_run, OptimizationRun):
            raise TypeError("optimization_run must be an OptimizationRun.")
        return self.reporting_service.run(optimization_run)


@dataclass(frozen=True, slots=True)
class OptimizationReportingRouter:
    """Route one completed run to one injected format-specific reporting facade."""

    registrations: tuple[
        tuple[OptimizationReportFormat, OptimizationReportingFacade[str]],
        ...,
    ]

    def __post_init__(self) -> None:
        """Require immutable unique format registrations without invoking them."""
        if not isinstance(self.registrations, tuple):
            raise TypeError("registrations must be a tuple.")
        formats: list[OptimizationReportFormat] = []
        for registration in self.registrations:
            if not isinstance(registration, tuple) or len(registration) != 2:
                raise TypeError(
                    "registrations must contain format and facade tuple pairs."
                )
            report_format, facade = registration
            if not isinstance(report_format, OptimizationReportFormat):
                raise TypeError(
                    "registration format must be an OptimizationReportFormat."
                )
            if facade is None or not callable(getattr(facade, "render_run", None)):
                raise TypeError(
                    "registration facade must define a callable render_run method."
                )
            formats.append(report_format)
        if len(set(formats)) != len(formats):
            raise ValueError("registrations must not contain duplicate formats.")

    def render_run(
        self,
        run: "OptimizationRun",
        report_format: OptimizationReportFormat,
    ) -> OptimizationResultRenderedReport[str]:
        """Delegate one exact run through one registered facade without fallback."""
        from src.engines.backtesting.optimization import OptimizationRun

        if not isinstance(run, OptimizationRun):
            raise TypeError("run must be an OptimizationRun.")
        if not isinstance(report_format, OptimizationReportFormat):
            raise TypeError("report_format must be an OptimizationReportFormat.")
        for registered_format, facade in self.registrations:
            if registered_format is report_format:
                return facade.render_run(run)
        raise ValueError("report_format is not registered.")


@dataclass(frozen=True, slots=True)
class OptimizationReportingCompositionRoot:
    """Assemble the complete injected selection-outcome reporting graphs."""

    selection_policy: SelectionPolicy

    def __post_init__(self) -> None:
        """Require one explicit selector without invoking it during composition."""
        if self.selection_policy is None:
            raise TypeError("selection_policy must not be None.")
        if not callable(getattr(self.selection_policy, "select", None)):
            raise TypeError("selection_policy must define a callable select method.")

    def build_router(self) -> OptimizationReportingRouter:
        """Build plain-text and Markdown paths without performing reporting."""
        plain_text_facade = OptimizationReportingFacade(
            OptimizationSelectionOutcomeReportingService(
                self.selection_policy,
                OptimizationSelectionOutcomeReportingWorkflow(
                    OptimizationSelectionOutcomeReportingPipeline(
                        PlainTextOptimizationSelectionOutcomeRenderer()
                    )
                ),
            )
        )
        markdown_facade = OptimizationReportingFacade(
            OptimizationSelectionOutcomeReportingService(
                self.selection_policy,
                OptimizationSelectionOutcomeReportingWorkflow(
                    OptimizationSelectionOutcomeReportingPipeline(
                        MarkdownOptimizationSelectionOutcomeRenderer()
                    )
                ),
            )
        )
        return OptimizationReportingRouter(
            (
                (OptimizationReportFormat.PLAIN_TEXT, plain_text_facade),
                (OptimizationReportFormat.MARKDOWN, markdown_facade),
            )
        )


@dataclass(frozen=True, slots=True)
class OptimizationExecutionReportingWorkflow:
    """Connect one injected optimization execution to one reporting router."""

    optimization_runner: OptimizationRunner
    reporting_router: OptimizationReportingRouter

    def __post_init__(self) -> None:
        """Require explicit execution and reporting collaborators only."""
        if self.optimization_runner is None:
            raise TypeError("optimization_runner must not be None.")
        if not callable(getattr(self.optimization_runner, "run", None)):
            raise TypeError("optimization_runner must define a callable run method.")
        if self.reporting_router is None:
            raise TypeError("reporting_router must not be None.")
        if not callable(getattr(self.reporting_router, "render_run", None)):
            raise TypeError(
                "reporting_router must define a callable render_run method."
            )

    def run(
        self,
        specification: OptimizationSpecification,
        report_format: OptimizationReportFormat,
    ) -> OptimizationResultRenderedReport[str]:
        """Execute once, then delegate the exact returned run to routing once."""
        optimization_run = self.optimization_runner.run(specification)
        return self.reporting_router.render_run(optimization_run, report_format)


@dataclass(frozen=True, slots=True)
class OptimizationExecutionReportingCompositionRoot:
    """Assemble one execution-to-reporting workflow from injected contracts."""

    optimization_runner: OptimizationRunner
    selection_policy: SelectionPolicy

    def __post_init__(self) -> None:
        """Require external execution and selection collaborators only."""
        if self.optimization_runner is None:
            raise TypeError("optimization_runner must not be None.")
        if not callable(getattr(self.optimization_runner, "run", None)):
            raise TypeError("optimization_runner must define a callable run method.")
        if self.selection_policy is None:
            raise TypeError("selection_policy must not be None.")
        if not callable(getattr(self.selection_policy, "select", None)):
            raise TypeError("selection_policy must define a callable select method.")

    def build_workflow(self) -> OptimizationExecutionReportingWorkflow:
        """Assemble reporting once without invoking execution or selection."""
        router = OptimizationReportingCompositionRoot(
            self.selection_policy
        ).build_router()
        return OptimizationExecutionReportingWorkflow(
            self.optimization_runner,
            router,
        )


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


@dataclass(frozen=True, slots=True)
class PlainTextOptimizationSelectionOutcomeRenderer:
    """Render complete selected outcomes as deterministic plain-text labels."""

    def render(
        self,
        report: OptimizationSelectionOutcomeReport,
    ) -> OptimizationResultRenderedReport[str]:
        """Return retained selected facts without Markdown or recalculation."""
        if not isinstance(report, OptimizationSelectionOutcomeReport):
            raise TypeError("report must be an OptimizationSelectionOutcomeReport.")
        lines = [
            "Optimization Selection Outcome",
            f"Selection Count: {report.selection_count}",
        ]
        for index, selected_outcome in enumerate(report.selected_outcomes, start=1):
            source_score = selected_outcome.source_score
            parameters = "; ".join(
                f"{name}={value}"
                for name, value in source_score.evaluation.candidate.assignments
            )
            lines.extend(
                (
                    f"Selected Outcome {index}:",
                    f"Rank: {selected_outcome.rank}",
                    f"Parameters: {parameters}",
                    f"Objective Score: {source_score.score}",
                    f"Objective Direction: {source_score.direction.value}",
                )
            )
        return OptimizationResultRenderedReport("\n".join(lines))


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
