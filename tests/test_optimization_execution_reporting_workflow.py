"""Contract tests for application orchestration from optimization to reporting."""

from dataclasses import FrozenInstanceError, dataclass
from unittest import TestCase

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
    OptimizationBudget,
    OptimizationConfiguration,
    OptimizationExecutionReportingWorkflow,
    OptimizationProgress,
    OptimizationReportFormat,
    OptimizationReportingCompositionRoot,
    OptimizationResultRenderedReport,
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


class OptimizationExecutionReportingWorkflowTests(TestCase):
    """Verify one exact optimization result flows into injected report routing."""

    def test_executes_once_routes_exact_run_format_and_rendered_result(self) -> None:
        specification = _specification()
        run = _run()
        runner = _RecordingRunner(run)
        expected = OptimizationResultRenderedReport("rendered")
        router = _RecordingRouter(expected)
        workflow = OptimizationExecutionReportingWorkflow(runner, router)

        result = workflow.run(specification, OptimizationReportFormat.PLAIN_TEXT)

        self.assertEqual(runner.call_count, 1)
        self.assertIs(runner.received_specification, specification)
        self.assertEqual(router.call_count, 1)
        self.assertIs(router.received_run, run)
        self.assertIs(router.received_format, OptimizationReportFormat.PLAIN_TEXT)
        self.assertIs(result, expected)

    def test_plain_text_and_markdown_flow_through_reporting(self) -> None:
        specification = _specification()
        runner = _RecordingRunner(_run())
        router = OptimizationReportingCompositionRoot(
            BestRankSelectionPolicy()
        ).build_router()
        workflow = OptimizationExecutionReportingWorkflow(runner, router)

        plain_text = workflow.run(specification, OptimizationReportFormat.PLAIN_TEXT)
        markdown = workflow.run(specification, OptimizationReportFormat.MARKDOWN)

        self.assertEqual(runner.call_count, 2)
        self.assertIs(runner.received_specification, specification)
        self.assertIn("Optimization Selection Outcome", plain_text.payload)
        self.assertNotIn("| Rank |", plain_text.payload)
        self.assertIn(
            "| Rank | Parameters | Objective Score | Direction |",
            markdown.payload,
        )

    def test_execution_and_router_failures_propagate(self) -> None:
        specification = _specification()
        router = _RecordingRouter(OptimizationResultRenderedReport("unused"))

        failing_runner = _FailingRunner()
        with self.assertRaisesRegex(RuntimeError, "execution failure"):
            OptimizationExecutionReportingWorkflow(failing_runner, router).run(
                specification,
                OptimizationReportFormat.PLAIN_TEXT,
            )
        self.assertEqual(failing_runner.call_count, 1)
        self.assertEqual(router.call_count, 0)

        runner = _RecordingRunner(_run())
        failing_router = _FailingRouter()
        with self.assertRaisesRegex(RuntimeError, "routing failure"):
            OptimizationExecutionReportingWorkflow(runner, failing_router).run(
                specification,
                OptimizationReportFormat.MARKDOWN,
            )
        self.assertEqual(runner.call_count, 1)
        self.assertEqual(failing_router.call_count, 1)

    def test_workflow_is_immutable_and_public_export_is_intentional(self) -> None:
        runner = _RecordingRunner(_run())
        router = _RecordingRouter(OptimizationResultRenderedReport("rendered"))
        workflow = OptimizationExecutionReportingWorkflow(runner, router)

        self.assertEqual(
            workflow,
            OptimizationExecutionReportingWorkflow(runner, router),
        )
        self.assertEqual(
            repr(workflow),
            repr(OptimizationExecutionReportingWorkflow(runner, router)),
        )
        with self.assertRaises(FrozenInstanceError):
            workflow.optimization_runner = runner  # type: ignore[misc]
        with self.assertRaisesRegex(TypeError, "optimization_runner"):
            OptimizationExecutionReportingWorkflow(
                None,
                router,
            )  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "reporting_router"):
            OptimizationExecutionReportingWorkflow(
                runner,
                None,
            )  # type: ignore[arg-type]

        from src.engines.backtesting import (
            OptimizationExecutionReportingWorkflow as PackageWorkflow,
        )
        from src.engines.backtesting.reporting import (
            OptimizationExecutionReportingWorkflow as ModuleWorkflow,
        )

        self.assertIs(PackageWorkflow, OptimizationExecutionReportingWorkflow)
        self.assertIs(ModuleWorkflow, OptimizationExecutionReportingWorkflow)


@dataclass
class _RecordingRunner:
    """Test-only canonical execution boundary retaining one exact specification."""

    result: OptimizationRun
    received_specification: OptimizationSpecification | None = None
    call_count: int = 0

    def run(self, specification: OptimizationSpecification) -> OptimizationRun:
        """Return the configured run after recording the exact input instance."""
        self.received_specification = specification
        self.call_count += 1
        return self.result


@dataclass
class _FailingRunner:
    """Test-only executor proving reporting does not run after execution failure."""

    call_count: int = 0

    def run(self, specification: OptimizationSpecification) -> OptimizationRun:
        """Fail after recording one invocation without producing a run."""
        del specification
        self.call_count += 1
        raise RuntimeError("execution failure")


@dataclass
class _RecordingRouter:
    """Test-only routing boundary retaining one exact run and report format."""

    result: OptimizationResultRenderedReport[str]
    received_run: OptimizationRun | None = None
    received_format: OptimizationReportFormat | None = None
    call_count: int = 0

    def render_run(
        self,
        run: OptimizationRun,
        report_format: OptimizationReportFormat,
    ) -> OptimizationResultRenderedReport[str]:
        """Return the configured rendered report after recording exact arguments."""
        self.received_run = run
        self.received_format = report_format
        self.call_count += 1
        return self.result


@dataclass
class _FailingRouter:
    """Test-only router proving routing failures propagate unchanged."""

    call_count: int = 0

    def render_run(
        self,
        run: OptimizationRun,
        report_format: OptimizationReportFormat,
    ) -> OptimizationResultRenderedReport[str]:
        """Fail after one exact routing invocation."""
        del run, report_format
        self.call_count += 1
        raise RuntimeError("routing failure")


class _SkippedExecutionEngine:
    """Minimal execution dependency for structural completed optimization runs."""

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Return one skipped result without executing a trade."""
        return ExecutionResult(request, ExecutionStatus.SKIPPED)


def _specification() -> OptimizationSpecification:
    """Build one existing canonical optimization input without execution."""
    return OptimizationSpecification(
        ParameterSpace((DiscreteParameter("orb_minutes", (15,)),)),
        OptimizationConfiguration(
            ObjectiveDirection.MAXIMIZE,
            BestRankSelectionPolicy(),
        ),
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
