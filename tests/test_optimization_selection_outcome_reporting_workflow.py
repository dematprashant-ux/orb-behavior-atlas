"""Contract tests for end-to-end completed selection outcome reporting."""

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
    OptimizationSelectionOutcomeReportingWorkflow,
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


class OptimizationSelectionOutcomeReportingWorkflowTests(TestCase):
    """Verify direct composition of completed run and selection artifacts."""

    def test_workflow_constructs_one_exact_report_and_returns_pipeline_result(
        self,
    ) -> None:
        run, selection = _run_and_selection((3.0, 3.0), selected_count=2)
        expected = OptimizationResultRenderedReport(("rendered",))
        pipeline = _RecordingPipeline(expected)
        workflow = OptimizationSelectionOutcomeReportingWorkflow(pipeline)

        with patch.object(
            OptimizationResultReport,
            "from_run_and_selection",
            wraps=OptimizationResultReport.from_run_and_selection,
        ) as factory:
            result = workflow.run(run, selection)

        factory.assert_called_once_with(run, selection)
        self.assertIs(workflow.reporting_pipeline, pipeline)
        self.assertEqual(pipeline.call_count, 1)
        self.assertIs(pipeline.received_report.run, run)
        self.assertIs(pipeline.received_report.selection, selection)
        self.assertIs(result, expected)

    def test_empty_unique_and_tied_selections_are_delegated_without_inspection(
        self,
    ) -> None:
        for scores, selected_count in (((), 0), ((3.0,), 1), ((3.0, 3.0), 2)):
            with self.subTest(scores=scores):
                run, selection = _run_and_selection(scores, selected_count)
                pipeline = _RecordingPipeline(OptimizationResultRenderedReport("ok"))

                result = OptimizationSelectionOutcomeReportingWorkflow(
                    pipeline
                ).run(run, selection)

                self.assertIs(result, pipeline.result)
                self.assertEqual(pipeline.call_count, 1)
                self.assertIs(pipeline.received_report.run, run)
                self.assertIs(pipeline.received_report.selection, selection)

    def test_workflow_is_immutable_deterministic_and_executes_no_other_stage(
        self,
    ) -> None:
        run, selection = _run_and_selection((2.0, 1.0), selected_count=1)
        pipeline = _RecordingPipeline(OptimizationResultRenderedReport("rendered"))
        workflow = OptimizationSelectionOutcomeReportingWorkflow(pipeline)

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
            first = workflow.run(run, selection)
            second = workflow.run(run, selection)

        self.assertEqual(first, second)
        self.assertEqual(pipeline.call_count, 2)
        self.assertEqual(
            repr(workflow),
            repr(OptimizationSelectionOutcomeReportingWorkflow(pipeline)),
        )
        with self.assertRaises(FrozenInstanceError):
            workflow.reporting_pipeline = pipeline  # type: ignore[misc]

    def test_invalid_inputs_and_failures_propagate_without_partial_output(self) -> None:
        run, selection = _run_and_selection((1.0,), selected_count=1)
        pipeline = _RecordingPipeline(OptimizationResultRenderedReport("rendered"))
        workflow = OptimizationSelectionOutcomeReportingWorkflow(pipeline)

        with self.assertRaisesRegex(TypeError, "reporting_pipeline"):
            OptimizationSelectionOutcomeReportingWorkflow(
                None
            )  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "reporting_pipeline"):
            OptimizationSelectionOutcomeReportingWorkflow(
                object()
            )  # type: ignore[arg-type]
        for invalid_run, invalid_selection in (
            (None, selection),
            (
                OptimizationResultReport.from_run_and_selection(run, selection),
                selection,
            ),
            (run, None),
            (run, run.ranking),
            ({}, selection),
            ("run", selection),
        ):
            with self.subTest(
                value=(invalid_run, invalid_selection),
            ), self.assertRaisesRegex(
                TypeError,
                "optimization_run|selection",
            ):
                workflow.run(invalid_run, invalid_selection)  # type: ignore[arg-type]

        mismatched_run, mismatched_selection = _run_and_selection((2.0,), 1)
        with self.assertRaisesRegex(ValueError, "exact ranking"):
            workflow.run(run, mismatched_selection)
        self.assertEqual(pipeline.call_count, 0)
        self.assertIsNot(mismatched_run.ranking, run.ranking)

        blocked_pipeline = _RecordingPipeline(OptimizationResultRenderedReport("x"))
        with patch.object(
            OptimizationResultReport,
            "from_run_and_selection",
            side_effect=RuntimeError("result failure"),
        ), self.assertRaisesRegex(RuntimeError, "result failure"):
            OptimizationSelectionOutcomeReportingWorkflow(blocked_pipeline).run(
                run,
                selection,
            )
        self.assertEqual(blocked_pipeline.call_count, 0)

        failing = _FailingPipeline()
        with self.assertRaisesRegex(RuntimeError, "pipeline failure"):
            OptimizationSelectionOutcomeReportingWorkflow(failing).run(run, selection)
        self.assertEqual(failing.call_count, 1)

    def test_public_export_is_intentional(self) -> None:
        from src.engines.backtesting import (
            OptimizationSelectionOutcomeReportingWorkflow as PackageWorkflow,
        )
        from src.engines.backtesting.reporting import (
            OptimizationSelectionOutcomeReportingWorkflow as ModuleWorkflow,
        )

        self.assertIs(PackageWorkflow, OptimizationSelectionOutcomeReportingWorkflow)
        self.assertIs(ModuleWorkflow, OptimizationSelectionOutcomeReportingWorkflow)


@dataclass
class _RecordingPipeline:
    """Test-only pipeline retaining one report and returning a fixed result."""

    result: OptimizationResultRenderedReport[object]
    received_report: OptimizationResultReport | None = None
    call_count: int = 0

    def render_report(
        self,
        result_report: OptimizationResultReport,
    ) -> OptimizationResultRenderedReport[object]:
        """Record one exact input and return the predetermined result."""
        self.received_report = result_report
        self.call_count += 1
        return self.result


@dataclass
class _FailingPipeline:
    """Test-only pipeline proving failure propagation without retries."""

    call_count: int = 0

    def render_report(
        self,
        result_report: OptimizationResultReport,
    ) -> OptimizationResultRenderedReport[object]:
        """Fail directly after recording one pipeline invocation."""
        del result_report
        self.call_count += 1
        raise RuntimeError("pipeline failure")


class _SkippedExecutionEngine:
    """Minimal execution dependency for structural candidate outcomes."""

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Return one skipped result without executing a trade."""
        return ExecutionResult(request, ExecutionStatus.SKIPPED)


def _run_and_selection(
    scores: tuple[float, ...],
    selected_count: int,
) -> tuple[OptimizationRun, ObjectiveSelection]:
    """Build completed immutable artifacts without executing a selection policy."""
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
    return run, selection


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
