"""Contract tests for selecting and reporting completed optimization runs."""

from dataclasses import FrozenInstanceError, dataclass
from unittest import TestCase
from unittest.mock import patch

from src.engines.backtesting import (
    BacktestContext,
    BacktestRun,
    BacktestStatus,
    BestRankSelectionPolicy,
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
    OptimizationSelectionOutcomeReportingService,
    OptimizationStrategyMetadata,
    OptimizationTerminationReason,
    RankedObjectiveScore,
    StandardObjectiveRanker,
    StandardOptimizationRunner,
)
from src.engines.execution import ExecutionRequest, ExecutionResult, ExecutionStatus
from src.engines.research import ORBBehaviorAtlas
from src.engines.strategy import CandidateParameterSet, ORBRuleStrategy


class OptimizationSelectionOutcomeReportingServiceTests(TestCase):
    """Verify canonical selection delegates exactly once into reporting."""

    def test_service_retains_dependencies_and_forwards_exact_identities(self) -> None:
        run = _run((3.0, 1.0))
        selection = ObjectiveSelection(run.ranking, run.ranking.ranked_scores[:1])
        selector = _RecordingSelector(selection)
        expected = OptimizationResultRenderedReport(("rendered",))
        workflow = _RecordingWorkflow(expected)
        service = OptimizationSelectionOutcomeReportingService(selector, workflow)

        result = service.run(run)

        self.assertIs(service.selection_policy, selector)
        self.assertIs(service.reporting_workflow, workflow)
        self.assertEqual(selector.call_count, 1)
        self.assertIs(selector.received_ranking, run.ranking)
        self.assertEqual(workflow.call_count, 1)
        self.assertIs(workflow.received_run, run)
        self.assertIs(workflow.received_selection, selection)
        self.assertIs(result, expected)

    def test_existing_policy_preserves_empty_unique_and_tied_selection_semantics(
        self,
    ) -> None:
        for scores, expected_count in (((), 0), ((3.0,), 1), ((3.0, 3.0, 1.0), 2)):
            with self.subTest(scores=scores):
                workflow = _RecordingWorkflow(OptimizationResultRenderedReport("ok"))
                run = _run(scores)

                result = OptimizationSelectionOutcomeReportingService(
                    BestRankSelectionPolicy(),
                    workflow,
                ).run(run)

                self.assertIs(result, workflow.result)
                self.assertEqual(workflow.call_count, 1)
                self.assertIs(workflow.received_run, run)
                self.assertIs(workflow.received_selection.ranking, run.ranking)
                self.assertEqual(
                    len(workflow.received_selection.selected_scores),
                    expected_count,
                )

    def test_service_is_immutable_deterministic_and_does_not_execute_other_stages(
        self,
    ) -> None:
        run = _run((2.0, 1.0))
        selection = ObjectiveSelection(run.ranking, run.ranking.ranked_scores[:1])
        selector = _RecordingSelector(selection)
        workflow = _RecordingWorkflow(OptimizationResultRenderedReport("rendered"))
        service = OptimizationSelectionOutcomeReportingService(selector, workflow)

        with patch.object(
            StandardOptimizationRunner,
            "run",
            side_effect=AssertionError("optimization must not execute"),
        ), patch.object(
            StandardObjectiveRanker,
            "rank",
            side_effect=AssertionError("ranking must not execute"),
        ):
            first = service.run(run)
            second = service.run(run)

        self.assertEqual(first, second)
        self.assertEqual(selector.call_count, 2)
        self.assertEqual(workflow.call_count, 2)
        self.assertEqual(
            repr(service),
            repr(OptimizationSelectionOutcomeReportingService(selector, workflow)),
        )
        with self.assertRaises(FrozenInstanceError):
            service.selection_policy = selector  # type: ignore[misc]

    def test_invalid_inputs_and_failures_propagate_without_partial_output(self) -> None:
        run = _run((1.0,))
        selection = ObjectiveSelection(run.ranking, run.ranking.ranked_scores)
        selector = _RecordingSelector(selection)
        workflow = _RecordingWorkflow(OptimizationResultRenderedReport("rendered"))
        service = OptimizationSelectionOutcomeReportingService(selector, workflow)

        with self.assertRaisesRegex(TypeError, "selection_policy"):
            OptimizationSelectionOutcomeReportingService(
                None,
                workflow,
            )  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "reporting_workflow"):
            OptimizationSelectionOutcomeReportingService(
                selector,
                None,
            )  # type: ignore[arg-type]
        for value in (
            None,
            run.ranking,
            selection,
            OptimizationResultReport.from_run_and_selection(run, selection),
            OptimizationSelectionOutcomeReport.from_result_report(
                OptimizationResultReport.from_run_and_selection(run, selection)
            ),
            {},
            "run",
        ):
            with self.subTest(value=value), self.assertRaisesRegex(
                TypeError,
                "optimization_run",
            ):
                service.run(value)  # type: ignore[arg-type]

        failing_selector = _FailingSelector()
        blocked_workflow = _RecordingWorkflow(OptimizationResultRenderedReport("x"))
        with self.assertRaisesRegex(RuntimeError, "selection failure"):
            OptimizationSelectionOutcomeReportingService(
                failing_selector,
                blocked_workflow,
            ).run(run)
        self.assertEqual(failing_selector.call_count, 1)
        self.assertEqual(blocked_workflow.call_count, 0)

        invalid_selector = _InvalidSelector()
        with self.assertRaisesRegex(TypeError, "ObjectiveSelection"):
            OptimizationSelectionOutcomeReportingService(
                invalid_selector,
                blocked_workflow,
            ).run(run)
        self.assertEqual(blocked_workflow.call_count, 0)

        failing_workflow = _FailingWorkflow()
        with self.assertRaisesRegex(RuntimeError, "workflow failure"):
            OptimizationSelectionOutcomeReportingService(
                selector,
                failing_workflow,
            ).run(run)
        self.assertEqual(selector.call_count, 1)
        self.assertEqual(failing_workflow.call_count, 1)

    def test_public_export_is_intentional(self) -> None:
        from src.engines.backtesting import (
            OptimizationSelectionOutcomeReportingService as PackageService,
        )
        from src.engines.backtesting.reporting import (
            OptimizationSelectionOutcomeReportingService as ModuleService,
        )

        self.assertIs(PackageService, OptimizationSelectionOutcomeReportingService)
        self.assertIs(ModuleService, OptimizationSelectionOutcomeReportingService)


@dataclass
class _RecordingSelector:
    """Test-only selector retaining the exact ranking it receives."""

    result: ObjectiveSelection
    received_ranking: ObjectiveRanking | None = None
    call_count: int = 0

    def select(self, ranking: ObjectiveRanking) -> ObjectiveSelection:
        """Record one exact ranking and return the predetermined selection."""
        self.received_ranking = ranking
        self.call_count += 1
        return self.result


@dataclass
class _FailingSelector:
    """Test-only selector proving selection failures stop reporting."""

    call_count: int = 0

    def select(self, ranking: ObjectiveRanking) -> ObjectiveSelection:
        """Fail directly after recording one selection invocation."""
        del ranking
        self.call_count += 1
        raise RuntimeError("selection failure")


class _InvalidSelector:
    """Test-only selector returning an invalid result without coercion."""

    def select(self, ranking: ObjectiveRanking) -> object:
        """Return an invalid value after accepting the supplied ranking."""
        del ranking
        return object()


@dataclass
class _RecordingWorkflow:
    """Test-only workflow retaining its exact upstream artifacts."""

    result: OptimizationResultRenderedReport[object]
    received_run: OptimizationRun | None = None
    received_selection: ObjectiveSelection | None = None
    call_count: int = 0

    def run(
        self,
        optimization_run: OptimizationRun,
        selection: ObjectiveSelection,
    ) -> OptimizationResultRenderedReport[object]:
        """Record one exact run-selection pair and return a fixed result."""
        self.received_run = optimization_run
        self.received_selection = selection
        self.call_count += 1
        return self.result


@dataclass
class _FailingWorkflow:
    """Test-only workflow proving errors propagate without reselection."""

    call_count: int = 0

    def run(
        self,
        optimization_run: OptimizationRun,
        selection: ObjectiveSelection,
    ) -> OptimizationResultRenderedReport[object]:
        """Fail directly after recording one reporting invocation."""
        del optimization_run, selection
        self.call_count += 1
        raise RuntimeError("workflow failure")


class _SkippedExecutionEngine:
    """Minimal execution dependency for structural candidate outcomes."""

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Return one skipped result without executing a trade."""
        return ExecutionResult(request, ExecutionStatus.SKIPPED)


def _run(scores: tuple[float, ...]) -> OptimizationRun:
    """Build a completed immutable run without executing an optimizer."""
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
    initial_selection = ObjectiveSelection(ranking)
    return OptimizationRun(
        OptimizationSearchRun(
            OptimizationStrategyMetadata("test"),
            tuple(score.evaluation for score in objective_scores),
            OptimizationProgress(len(objective_scores), len(objective_scores)),
            OptimizationTerminationReason.SEARCH_SPACE_EXHAUSTED,
            ConstraintDiagnostics(),
        ),
        objective_scores,
        ranking,
        initial_selection,
    )


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
