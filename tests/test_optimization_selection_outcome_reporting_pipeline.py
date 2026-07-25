"""Contract tests for reporting existing complete optimization selections."""

from dataclasses import FrozenInstanceError, dataclass
from unittest import TestCase
from unittest.mock import patch

from src.engines.backtesting import (
    BacktestContext,
    BacktestRun,
    BacktestStatus,
    CandidateEvaluation,
    ConstraintDiagnostics,
    ObjectiveDirection,
    ObjectiveRanking,
    ObjectiveScore,
    ObjectiveSelection,
    OptimizationProgress,
    OptimizationResultRenderedReport,
    OptimizationResultReport,
    OptimizationRun,
    OptimizationSearchRun,
    OptimizationSelectionOutcomeReport,
    OptimizationSelectionOutcomeReportingPipeline,
    OptimizationStrategyMetadata,
    OptimizationTerminationReason,
    RankedObjectiveScore,
    StandardObjectiveRanker,
    StandardOptimizationRunner,
    TopRankedSelectionPolicy,
)
from src.engines.execution import ExecutionRequest, ExecutionResult, ExecutionStatus
from src.engines.research import ORBBehaviorAtlas
from src.engines.strategy import CandidateParameterSet, ORBRuleStrategy


class OptimizationSelectionOutcomeReportingPipelineTests(TestCase):
    """Verify canonical outcome composition and direct renderer delegation only."""

    def test_pipeline_uses_factory_once_and_returns_renderer_result_by_identity(
        self,
    ) -> None:
        result_report = _result_report((3.0, 3.0, 1.0), selected_count=2)
        expected = OptimizationResultRenderedReport(("rendered",))
        renderer = _RecordingRenderer(expected)
        pipeline = OptimizationSelectionOutcomeReportingPipeline(renderer)

        with patch.object(
            OptimizationSelectionOutcomeReport,
            "from_result_report",
            wraps=OptimizationSelectionOutcomeReport.from_result_report,
        ) as factory:
            result = pipeline.render_report(result_report)

        factory.assert_called_once_with(result_report)
        self.assertIs(pipeline.renderer, renderer)
        self.assertEqual(renderer.call_count, 1)
        self.assertIs(result, expected)
        self.assertIsNotNone(renderer.received_report)
        self.assertIs(renderer.received_report.result_report, result_report)
        self.assertIs(
            renderer.received_report.selected_outcomes,
            result_report.selection.selected_scores,
        )
        self.assertEqual(renderer.received_report.selection_count, 2)
        self.assertIs(
            renderer.received_report.selected_outcomes[0],
            result_report.selection.selected_scores[0],
        )
        self.assertIs(
            renderer.received_report.selected_outcomes[1],
            result_report.selection.selected_scores[1],
        )

    def test_empty_unique_and_tied_selections_flow_without_pipeline_logic(
        self,
    ) -> None:
        for scores, selected_count in (((), 0), ((3.0,), 1), ((3.0, 3.0), 2)):
            with self.subTest(scores=scores):
                renderer = _RecordingRenderer(OptimizationResultRenderedReport("ok"))
                result_report = _result_report(scores, selected_count)

                result = OptimizationSelectionOutcomeReportingPipeline(
                    renderer
                ).render_report(result_report)

                self.assertIs(result, renderer.result)
                self.assertEqual(renderer.call_count, 1)
                self.assertIsNotNone(renderer.received_report)
                self.assertEqual(
                    renderer.received_report.selection_count,
                    selected_count,
                )
                self.assertEqual(
                    renderer.received_report.selected_outcomes,
                    result_report.selection.selected_scores,
                )

    def test_pipeline_is_immutable_deterministic_and_executes_no_other_stage(
        self,
    ) -> None:
        result_report = _result_report((2.0, 1.0), selected_count=1)
        renderer = _RecordingRenderer(OptimizationResultRenderedReport("rendered"))
        pipeline = OptimizationSelectionOutcomeReportingPipeline(renderer)

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
            first = pipeline.render_report(result_report)
            second = pipeline.render_report(result_report)

        self.assertEqual(first, second)
        self.assertEqual(renderer.call_count, 2)
        self.assertEqual(
            repr(pipeline),
            repr(OptimizationSelectionOutcomeReportingPipeline(renderer)),
        )
        self.assertIs(result_report.selection, result_report.run.selection)
        with self.assertRaises(FrozenInstanceError):
            pipeline.renderer = renderer  # type: ignore[misc]

    def test_invalid_inputs_and_failures_propagate_without_partial_output(self) -> None:
        result_report = _result_report((1.0,), selected_count=1)
        renderer = _RecordingRenderer(OptimizationResultRenderedReport("rendered"))
        pipeline = OptimizationSelectionOutcomeReportingPipeline(renderer)

        with self.assertRaisesRegex(TypeError, "renderer"):
            OptimizationSelectionOutcomeReportingPipeline(
                None
            )  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "renderer"):
            OptimizationSelectionOutcomeReportingPipeline(
                object()
            )  # type: ignore[arg-type]
        for value in (
            None,
            result_report.run,
            result_report.selection,
            result_report.selection.ranking,
            OptimizationSelectionOutcomeReport.from_result_report(result_report),
            (),
            {},
            "result_report",
        ):
            with self.subTest(value=value), self.assertRaisesRegex(
                TypeError,
                "result_report",
            ):
                pipeline.render_report(value)  # type: ignore[arg-type]

        blocked_renderer = _RecordingRenderer(OptimizationResultRenderedReport("x"))
        with patch.object(
            OptimizationSelectionOutcomeReport,
            "from_result_report",
            side_effect=RuntimeError("outcome failure"),
        ), self.assertRaisesRegex(RuntimeError, "outcome failure"):
            OptimizationSelectionOutcomeReportingPipeline(
                blocked_renderer
            ).render_report(result_report)
        self.assertEqual(blocked_renderer.call_count, 0)

        failing = _FailingRenderer()
        with self.assertRaisesRegex(RuntimeError, "renderer failure"):
            OptimizationSelectionOutcomeReportingPipeline(failing).render_report(
                result_report
            )
        self.assertEqual(failing.call_count, 1)

    def test_public_export_is_intentional(self) -> None:
        from src.engines.backtesting import (
            OptimizationSelectionOutcomeReportingPipeline as PackagePipeline,
        )
        from src.engines.backtesting.reporting import (
            OptimizationSelectionOutcomeReportingPipeline as ModulePipeline,
        )

        self.assertIs(PackagePipeline, OptimizationSelectionOutcomeReportingPipeline)
        self.assertIs(ModulePipeline, OptimizationSelectionOutcomeReportingPipeline)


@dataclass
class _RecordingRenderer:
    """Test-only outcome renderer retaining its exact received report."""

    result: OptimizationResultRenderedReport[object]
    received_report: OptimizationSelectionOutcomeReport | None = None
    call_count: int = 0

    def render(
        self,
        report: OptimizationSelectionOutcomeReport,
    ) -> OptimizationResultRenderedReport[object]:
        """Record the canonical outcome once and return a fixed result."""
        self.received_report = report
        self.call_count += 1
        return self.result


@dataclass
class _FailingRenderer:
    """Test-only renderer proving failures propagate without retries."""

    call_count: int = 0

    def render(
        self,
        report: OptimizationSelectionOutcomeReport,
    ) -> OptimizationResultRenderedReport[object]:
        """Fail directly after recording one renderer invocation."""
        del report
        self.call_count += 1
        raise RuntimeError("renderer failure")


class _SkippedExecutionEngine:
    """Minimal execution dependency for structural candidate outcomes."""

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Return one skipped result without executing a trade."""
        return ExecutionResult(request, ExecutionStatus.SKIPPED)


def _result_report(
    scores: tuple[float, ...],
    selected_count: int,
) -> OptimizationResultReport:
    """Build existing immutable selection artifacts without running a policy."""
    objective_scores = tuple(
        _objective_score(index, value) for index, value in enumerate(scores)
    )
    ranking = ObjectiveRanking(
        ObjectiveDirection.MAXIMIZE,
        tuple(
            RankedObjectiveScore(score, index)
            for index, score in enumerate(objective_scores, start=1)
        ),
    )
    selection = ObjectiveSelection(ranking, ranking.ranked_scores[:selected_count])
    run = OptimizationRun(
        OptimizationSearchRun(
            OptimizationStrategyMetadata("test"),
            tuple(score.evaluation for score in objective_scores),
            OptimizationProgress(len(objective_scores), len(objective_scores)),
            OptimizationTerminationReason.SEARCH_SPACE_EXHAUSTED,
            ConstraintDiagnostics(),
        ),
        objective_scores,
        ranking,
        selection,
    )
    return OptimizationResultReport.from_run_and_selection(run, selection)


def _objective_score(index: int, value: float) -> ObjectiveScore:
    """Create one existing score fixture without objective evaluation."""
    context = BacktestContext(
        ORBBehaviorAtlas(records=()),
        ORBRuleStrategy(),
        _SkippedExecutionEngine(),
    )
    evaluation = CandidateEvaluation(
        CandidateParameterSet((("candidate", index),)),
        BacktestRun(context, BacktestStatus.COMPLETED),
    )
    return ObjectiveScore(evaluation, value, ObjectiveDirection.MAXIMIZE)
