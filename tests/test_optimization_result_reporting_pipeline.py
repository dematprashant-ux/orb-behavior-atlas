"""Contract tests for immutable rendering of completed optimization results."""

from dataclasses import dataclass
from unittest import TestCase
from unittest.mock import patch

from src.engines.backtesting import (
    ConstraintDiagnostics,
    ObjectiveDirection,
    ObjectiveRanking,
    ObjectiveSelection,
    OptimizationProgress,
    OptimizationResultRenderedReport,
    OptimizationResultReport,
    OptimizationResultReportRenderer,
    OptimizationResultReportingPipeline,
    OptimizationRun,
    OptimizationSearchRun,
    OptimizationStrategyMetadata,
    OptimizationTerminationReason,
    StandardObjectiveRanker,
    StandardOptimizationRunner,
    TopRankedSelectionPolicy,
)


class OptimizationResultReportingPipelineTests(TestCase):
    """Verify direct renderer delegation without optimization-stage execution."""

    def test_pipeline_injects_renderer_and_returns_its_exact_result(self) -> None:
        report = _report()
        expected = OptimizationResultRenderedReport(("rendered",))
        renderer = _RecordingRenderer(expected)
        pipeline = OptimizationResultReportingPipeline(renderer)

        result = pipeline.render_report(report)

        self.assertIs(pipeline.renderer, renderer)
        self.assertEqual(renderer.call_count, 1)
        self.assertIs(renderer.received_report, report)
        self.assertIs(result, expected)

    def test_pipeline_is_deterministic_and_does_not_execute_other_stages(self) -> None:
        report = _report()
        run = report.run
        expected = OptimizationResultRenderedReport("rendered")
        renderer = _RecordingRenderer(expected)
        pipeline = OptimizationResultReportingPipeline(renderer)

        with patch.object(
            StandardOptimizationRunner,
            "run",
            side_effect=AssertionError("optimization must not execute"),
        ), patch.object(
            StandardObjectiveRanker,
            "rank",
            side_effect=AssertionError("ranking must not execute"),
        ), patch.object(
            TopRankedSelectionPolicy,
            "select",
            side_effect=AssertionError("selection must not execute"),
        ):
            first = pipeline.render_report(report)
            second = pipeline.render_report(report)

        self.assertIs(first, expected)
        self.assertIs(second, expected)
        self.assertEqual(renderer.call_count, 2)
        self.assertIs(report.run, run)
        self.assertIs(report.selection, run.selection)

    def test_invalid_dependencies_reports_and_renderer_failures_propagate(self) -> None:
        renderer = _RecordingRenderer(OptimizationResultRenderedReport("rendered"))
        pipeline = OptimizationResultReportingPipeline(renderer)

        with self.assertRaisesRegex(TypeError, "renderer"):
            OptimizationResultReportingPipeline(None)  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "renderer"):
            OptimizationResultReportingPipeline(object())  # type: ignore[arg-type]
        for value in (None, (), {}, "report"):
            with self.subTest(value=value), self.assertRaisesRegex(TypeError, "report"):
                pipeline.render_report(value)  # type: ignore[arg-type]

        failing = _FailingRenderer()
        with self.assertRaisesRegex(RuntimeError, "renderer failure"):
            OptimizationResultReportingPipeline(failing).render_report(_report())
        self.assertEqual(failing.call_count, 1)

    def test_public_exports_are_intentional(self) -> None:
        from src.engines.backtesting import (
            OptimizationResultRenderedReport as PackageRendered,
        )
        from src.engines.backtesting import (
            OptimizationResultReportRenderer as PackageRenderer,
        )
        from src.engines.backtesting import (
            OptimizationResultReportingPipeline as PackagePipeline,
        )
        from src.engines.backtesting.reporting import (
            OptimizationResultRenderedReport as ModuleRendered,
        )
        from src.engines.backtesting.reporting import (
            OptimizationResultReportRenderer as ModuleRenderer,
        )
        from src.engines.backtesting.reporting import (
            OptimizationResultReportingPipeline as ModulePipeline,
        )

        self.assertIs(PackageRendered, OptimizationResultRenderedReport)
        self.assertIs(PackageRenderer, OptimizationResultReportRenderer)
        self.assertIs(PackagePipeline, OptimizationResultReportingPipeline)
        self.assertIs(ModuleRendered, OptimizationResultRenderedReport)
        self.assertIs(ModuleRenderer, OptimizationResultReportRenderer)
        self.assertIs(ModulePipeline, OptimizationResultReportingPipeline)


@dataclass
class _RecordingRenderer:
    """Test-only renderer retaining its exact input and fixed output."""

    result: OptimizationResultRenderedReport[object]
    received_report: OptimizationResultReport | None = None
    call_count: int = 0

    def render(
        self,
        report: OptimizationResultReport,
    ) -> OptimizationResultRenderedReport[object]:
        """Record one input identity and return the predetermined result."""
        self.received_report = report
        self.call_count += 1
        return self.result


@dataclass
class _FailingRenderer:
    """Test-only renderer proving direct failure propagation without retries."""

    call_count: int = 0

    def render(
        self,
        report: OptimizationResultReport,
    ) -> OptimizationResultRenderedReport[object]:
        """Fail directly after recording one attempt."""
        del report
        self.call_count += 1
        raise RuntimeError("renderer failure")


def _report() -> OptimizationResultReport:
    """Return one existing immutable result report without optimization execution."""
    ranking = ObjectiveRanking(ObjectiveDirection.MAXIMIZE)
    run = OptimizationRun(
        OptimizationSearchRun(
            OptimizationStrategyMetadata("test"),
            (),
            OptimizationProgress(0, 0),
            OptimizationTerminationReason.SEARCH_SPACE_EXHAUSTED,
            ConstraintDiagnostics(),
        ),
        (),
        ranking,
        ObjectiveSelection(ranking),
    )
    return OptimizationResultReport.from_run_and_selection(run, run.selection)
