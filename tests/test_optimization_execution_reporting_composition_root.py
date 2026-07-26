"""Contract tests for composing end-to-end optimization execution reporting."""

from dataclasses import FrozenInstanceError, dataclass
from unittest import TestCase

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
    OptimizationBudget,
    OptimizationConfiguration,
    OptimizationExecutionReportingCompositionRoot,
    OptimizationExecutionReportingWorkflow,
    OptimizationProgress,
    OptimizationReportFormat,
    OptimizationRun,
    OptimizationSearchRun,
    OptimizationSpecification,
    OptimizationStrategyMetadata,
    OptimizationTerminationReason,
    RankedObjectiveScore,
)
from src.engines.execution import ExecutionRequest, ExecutionResult, ExecutionStatus
from src.engines.research import ORBBehaviorAtlas
from src.engines.strategy import (
    CandidateParameterSet,
    DiscreteParameter,
    ORBRuleStrategy,
    ParameterSpace,
)


class OptimizationExecutionReportingCompositionRootTests(TestCase):
    """Verify composition connects external execution to both reporting formats."""

    def test_build_workflow_retains_dependencies_without_calls(self) -> None:
        runner = _RecordingRunner(_run())
        selector = _RecordingSelector()
        root = OptimizationExecutionReportingCompositionRoot(runner, selector)

        workflow = root.build_workflow()

        self.assertIsInstance(workflow, OptimizationExecutionReportingWorkflow)
        self.assertIs(workflow.optimization_runner, runner)
        for _, facade in workflow.reporting_router.registrations:
            self.assertIs(facade.reporting_service.selection_policy, selector)
        self.assertEqual(runner.call_count, 0)
        self.assertEqual(selector.call_count, 0)

    def test_assembled_workflow_supports_plain_text_and_markdown(self) -> None:
        run = _run()
        runner = _RecordingRunner(run)
        selector = _RecordingSelector()
        workflow = OptimizationExecutionReportingCompositionRoot(
            runner,
            selector,
        ).build_workflow()
        specification = _specification()

        plain_text = workflow.run(specification, OptimizationReportFormat.PLAIN_TEXT)
        markdown = workflow.run(specification, OptimizationReportFormat.MARKDOWN)

        self.assertEqual(runner.call_count, 2)
        self.assertIs(runner.received_specification, specification)
        self.assertEqual(selector.received_rankings, (run.ranking, run.ranking))
        self.assertIn("Optimization Selection Outcome", plain_text.payload)
        self.assertNotIn("| Rank |", plain_text.payload)
        self.assertIn(
            "| Rank | Parameters | Objective Score | Direction |",
            markdown.payload,
        )

    def test_composition_is_immutable_deterministic_and_publicly_exported(self) -> None:
        runner = _RecordingRunner(_run())
        selector = _RecordingSelector()
        root = OptimizationExecutionReportingCompositionRoot(runner, selector)

        first = root.build_workflow()
        second = root.build_workflow()

        self.assertEqual(first, second)
        self.assertEqual(repr(first), repr(second))
        self.assertEqual(runner.call_count, 0)
        self.assertEqual(selector.call_count, 0)
        with self.assertRaises(FrozenInstanceError):
            root.optimization_runner = runner  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            root.selection_policy = selector  # type: ignore[misc]

        from src.engines.backtesting import (
            OptimizationExecutionReportingCompositionRoot as PackageRoot,
        )
        from src.engines.backtesting.reporting import (
            OptimizationExecutionReportingCompositionRoot as ModuleRoot,
        )

        self.assertIs(PackageRoot, OptimizationExecutionReportingCompositionRoot)
        self.assertIs(ModuleRoot, OptimizationExecutionReportingCompositionRoot)

    def test_invalid_collaborators_are_rejected_without_hidden_defaults(self) -> None:
        runner = _RecordingRunner(_run())
        selector = _RecordingSelector()

        with self.assertRaisesRegex(TypeError, "optimization_runner"):
            OptimizationExecutionReportingCompositionRoot(
                None,
                selector,
            )  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "selection_policy"):
            OptimizationExecutionReportingCompositionRoot(
                runner,
                None,
            )  # type: ignore[arg-type]


@dataclass
class _RecordingRunner:
    """Test-only execution boundary preserving one exact supplied specification."""

    result: OptimizationRun
    received_specification: OptimizationSpecification | None = None
    call_count: int = 0

    def run(self, specification: OptimizationSpecification) -> OptimizationRun:
        """Return the fixed run after recording the exact input identity."""
        self.received_specification = specification
        self.call_count += 1
        return self.result


@dataclass
class _RecordingSelector:
    """Test-only selector recording each exact ranking used for reporting."""

    received_rankings: tuple[ObjectiveRanking, ...] = ()
    call_count: int = 0

    def select(self, ranking: ObjectiveRanking) -> ObjectiveSelection:
        """Select retained leading entries without reranking the source ranking."""
        self.received_rankings += (ranking,)
        self.call_count += 1
        return ObjectiveSelection(ranking, ranking.ranked_scores[:1])


class _SkippedExecutionEngine:
    """Minimal execution dependency for structural completed optimization runs."""

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Return one skipped result without executing a trade."""
        return ExecutionResult(request, ExecutionStatus.SKIPPED)


def _specification() -> OptimizationSpecification:
    """Build one existing canonical optimization input without execution."""
    return OptimizationSpecification(
        ParameterSpace((DiscreteParameter("orb_minutes", (15,)),)),
        OptimizationConfiguration(ObjectiveDirection.MAXIMIZE, _RecordingSelector()),
        OptimizationBudget(1),
    )


def _run() -> OptimizationRun:
    """Build one existing completed run without executing optimization stages."""
    context = BacktestContext(
        ORBBehaviorAtlas(records=()),
        ORBRuleStrategy(),
        _SkippedExecutionEngine(),
    )
    evaluation = CandidateEvaluation(
        CandidateParameterSet((("orb_minutes", 15),)),
        BacktestRun(context, BacktestStatus.COMPLETED),
    )
    score = ObjectiveScore(evaluation, 3.0, ObjectiveDirection.MAXIMIZE)
    ranking = ObjectiveRanking(
        ObjectiveDirection.MAXIMIZE,
        (RankedObjectiveScore(score, 1),),
    )
    selection = ObjectiveSelection(ranking, ranking.ranked_scores)
    return OptimizationRun(
        OptimizationSearchRun(
            OptimizationStrategyMetadata("test"),
            (evaluation,),
            OptimizationProgress(1, 1),
            OptimizationTerminationReason.SEARCH_SPACE_EXHAUSTED,
            ConstraintDiagnostics(),
        ),
        (score,),
        ranking,
        selection,
    )
