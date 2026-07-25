"""Contract tests for end-to-end one-run optimization summary reporting."""

from dataclasses import dataclass
from unittest import TestCase
from unittest.mock import patch

from src.engines.backtesting import (
    ConstraintDiagnostics,
    HtmlOptimizationRunSummaryReportRenderer,
    MarkdownOptimizationRunSummaryReportRenderer,
    ObjectiveDirection,
    ObjectiveRanking,
    ObjectiveSelection,
    OptimizationProgress,
    OptimizationRun,
    OptimizationRunSummary,
    OptimizationRunSummaryAggregate,
    OptimizationRunSummaryRenderedReport,
    OptimizationRunSummaryReportingPipeline,
    OptimizationRunSummaryReport,
    OptimizationRunSummaryRates,
    OptimizationSearchRun,
    OptimizationStrategyMetadata,
    OptimizationTerminationReason,
    PlainTextOptimizationRunSummaryReportRenderer,
)


class OptimizationRunSummaryReportingPipelineTests(TestCase):
    """Verify one completed run flows through canonical reporting stages only."""

    def test_pipeline_retains_injected_renderer_and_returns_its_exact_result(
        self,
    ) -> None:
        expected = OptimizationRunSummaryRenderedReport(("rendered",))
        renderer = _RecordingRenderer(expected)
        pipeline = OptimizationRunSummaryReportingPipeline(renderer)

        result = pipeline.render_run(_run())

        self.assertIs(pipeline.renderer, renderer)
        self.assertEqual(renderer.call_count, 1)
        self.assertIsNotNone(renderer.received_report)
        self.assertIs(result, expected)

    def test_pipeline_uses_canonical_summary_factories_without_duplication(
        self,
    ) -> None:
        run = _run()
        summary = OptimizationRunSummary.from_run(run)
        renderer = _RecordingRenderer(OptimizationRunSummaryRenderedReport("output"))
        pipeline = OptimizationRunSummaryReportingPipeline(renderer)

        with patch.object(
            OptimizationRunSummary,
            "from_run",
            return_value=summary,
        ) as summary_factory, patch.object(
            OptimizationRunSummaryAggregate,
            "from_summaries",
            wraps=OptimizationRunSummaryAggregate.from_summaries,
        ) as aggregate_factory, patch.object(
            OptimizationRunSummaryRates,
            "from_aggregate",
            wraps=OptimizationRunSummaryRates.from_aggregate,
        ) as rates_factory, patch.object(
            OptimizationRunSummaryReport,
            "from_analysis",
            wraps=OptimizationRunSummaryReport.from_analysis,
        ) as report_factory:
            result = pipeline.render_run(run)

        summary_factory.assert_called_once_with(run)
        aggregate_factory.assert_called_once()
        rates_factory.assert_called_once()
        report_factory.assert_called_once()
        self.assertIs(renderer.received_report.analysis.summaries[0], summary)
        self.assertIs(result, renderer.result)

    def test_all_concrete_renderers_work_without_renderer_type_branching(self) -> None:
        run = _run()

        plain = OptimizationRunSummaryReportingPipeline(
            PlainTextOptimizationRunSummaryReportRenderer()
        ).render_run(run)
        markdown = OptimizationRunSummaryReportingPipeline(
            MarkdownOptimizationRunSummaryReportRenderer()
        ).render_run(run)
        html = OptimizationRunSummaryReportingPipeline(
            HtmlOptimizationRunSummaryReportRenderer()
        ).render_run(run)

        self.assertTrue(plain.payload.startswith("Optimization Run Summary"))
        self.assertTrue(markdown.payload.startswith("# Optimization Run Summary"))
        self.assertTrue(html.payload.startswith("<section>"))

    def test_pipeline_is_deterministic_and_does_not_mutate_supplied_run(self) -> None:
        run = _run()
        pipeline = OptimizationRunSummaryReportingPipeline(
            PlainTextOptimizationRunSummaryReportRenderer()
        )

        first = pipeline.render_run(run)
        second = pipeline.render_run(run)

        self.assertEqual(first, second)
        self.assertEqual(run.progress, OptimizationProgress(0, 0))
        self.assertEqual(run.constraint_diagnostics, ConstraintDiagnostics())

    def test_invalid_dependencies_or_runs_and_stage_failures_propagate(self) -> None:
        renderer = _RecordingRenderer(OptimizationRunSummaryRenderedReport("output"))
        pipeline = OptimizationRunSummaryReportingPipeline(renderer)

        with self.assertRaisesRegex(TypeError, "renderer"):
            OptimizationRunSummaryReportingPipeline(None)  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "renderer"):
            OptimizationRunSummaryReportingPipeline(object())  # type: ignore[arg-type]
        for value in (None, (), {}, "run"):
            with self.subTest(value=value), self.assertRaisesRegex(TypeError, "run"):
                pipeline.render_run(value)  # type: ignore[arg-type]
        with patch.object(
            OptimizationRunSummary,
            "from_run",
            side_effect=RuntimeError("summary failure"),
        ), self.assertRaisesRegex(RuntimeError, "summary failure"):
            pipeline.render_run(_run())
        self.assertEqual(renderer.call_count, 0)

    def test_renderer_failure_propagates_without_retry_and_public_export(self) -> None:
        renderer = _FailingRenderer()
        pipeline = OptimizationRunSummaryReportingPipeline(renderer)

        with self.assertRaisesRegex(RuntimeError, "renderer failure"):
            pipeline.render_run(_run())
        self.assertEqual(renderer.call_count, 1)

        from src.engines.backtesting import (
            OptimizationRunSummaryReportingPipeline as PackagePipeline,
        )
        from src.engines.backtesting.reporting import (
            OptimizationRunSummaryReportingPipeline as ModulePipeline,
        )

        self.assertIs(PackagePipeline, OptimizationRunSummaryReportingPipeline)
        self.assertIs(ModulePipeline, OptimizationRunSummaryReportingPipeline)


@dataclass
class _RecordingRenderer:
    """Test-only generic renderer recording the exact report it receives."""

    result: OptimizationRunSummaryRenderedReport[object]
    received_report: OptimizationRunSummaryReport | None = None
    call_count: int = 0

    def render(
        self,
        report: OptimizationRunSummaryReport,
    ) -> OptimizationRunSummaryRenderedReport[object]:
        """Retain one report reference and return the exact predetermined result."""
        self.received_report = report
        self.call_count += 1
        return self.result


@dataclass
class _FailingRenderer:
    """Test-only renderer that proves failures are propagated without retries."""

    call_count: int = 0

    def render(
        self,
        report: OptimizationRunSummaryReport,
    ) -> OptimizationRunSummaryRenderedReport[object]:
        """Fail directly without producing a rendered value."""
        self.call_count += 1
        raise RuntimeError("renderer failure")


def _run() -> OptimizationRun:
    """Return one completed empty optimization run without executing a strategy."""
    ranking = ObjectiveRanking(ObjectiveDirection.MAXIMIZE)
    search_run = OptimizationSearchRun(
        OptimizationStrategyMetadata("test"),
        (),
        OptimizationProgress(0, 0),
        OptimizationTerminationReason.SEARCH_SPACE_EXHAUSTED,
        ConstraintDiagnostics(),
    )
    return OptimizationRun(search_run, (), ranking, ObjectiveSelection(ranking))
