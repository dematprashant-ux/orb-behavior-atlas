"""Contract tests for deterministic optimization selection-outcome routing."""

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
    OptimizationReportFormat,
    OptimizationReportingRouter,
    OptimizationResultRenderedReport,
    OptimizationRun,
    OptimizationSearchRun,
    OptimizationStrategyMetadata,
    OptimizationTerminationReason,
    RankedObjectiveScore,
    StandardObjectiveRanker,
    StandardOptimizationRunner,
)
from src.engines.execution import ExecutionRequest, ExecutionResult, ExecutionStatus
from src.engines.research import ORBBehaviorAtlas
from src.engines.strategy import CandidateParameterSet, ORBRuleStrategy


class OptimizationReportingRouterTests(TestCase):
    """Verify one exact injected facade receives each routed completed run."""

    def test_plain_text_routes_once_without_invoking_markdown(self) -> None:
        run = _run()
        plain_text = _RecordingFacade(OptimizationResultRenderedReport("plain"))
        markdown = _RecordingFacade(OptimizationResultRenderedReport("markdown"))
        router = _router(plain_text, markdown)

        rendered = router.render_run(run, OptimizationReportFormat.PLAIN_TEXT)

        self.assertIs(rendered, plain_text.result)
        self.assertEqual(plain_text.call_count, 1)
        self.assertIs(plain_text.received_run, run)
        self.assertEqual(markdown.call_count, 0)

    def test_markdown_routes_once_without_invoking_plain_text(self) -> None:
        run = _run()
        plain_text = _RecordingFacade(OptimizationResultRenderedReport("plain"))
        markdown = _RecordingFacade(OptimizationResultRenderedReport("markdown"))
        router = _router(plain_text, markdown)

        rendered = router.render_run(run, OptimizationReportFormat.MARKDOWN)

        self.assertIs(rendered, markdown.result)
        self.assertEqual(markdown.call_count, 1)
        self.assertIs(markdown.received_run, run)
        self.assertEqual(plain_text.call_count, 0)

    def test_router_is_immutable_deterministic_and_only_delegates(self) -> None:
        run = _run()
        plain_text = _RecordingFacade(OptimizationResultRenderedReport("plain"))
        markdown = _RecordingFacade(OptimizationResultRenderedReport("markdown"))
        router = _router(plain_text, markdown)

        with patch.object(
            StandardOptimizationRunner,
            "run",
            side_effect=AssertionError("optimization must not execute"),
        ), patch.object(
            StandardObjectiveRanker,
            "rank",
            side_effect=AssertionError("ranking must not execute"),
        ):
            first = router.render_run(run, OptimizationReportFormat.PLAIN_TEXT)
            second = router.render_run(run, OptimizationReportFormat.PLAIN_TEXT)

        self.assertEqual(first, second)
        self.assertEqual(plain_text.call_count, 2)
        self.assertEqual(markdown.call_count, 0)
        self.assertEqual(router, _router(plain_text, markdown))
        self.assertEqual(repr(router), repr(_router(plain_text, markdown)))
        self.assertIsInstance(router.registrations, tuple)
        with self.assertRaises(FrozenInstanceError):
            router.registrations = ()  # type: ignore[misc]

    def test_invalid_unregistered_and_duplicate_formats_fail(self) -> None:
        run = _run()
        plain_text = _RecordingFacade(OptimizationResultRenderedReport("plain"))
        markdown = _RecordingFacade(OptimizationResultRenderedReport("markdown"))
        router = OptimizationReportingRouter(
            ((OptimizationReportFormat.PLAIN_TEXT, plain_text),)
        )

        for value in (None, "markdown", object()):
            with self.subTest(value=value), self.assertRaisesRegex(
                TypeError,
                "report_format",
            ):
                router.render_run(run, value)  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "not registered"):
            router.render_run(run, OptimizationReportFormat.MARKDOWN)
        self.assertEqual(plain_text.call_count, 0)
        self.assertEqual(markdown.call_count, 0)

        with self.assertRaisesRegex(ValueError, "duplicate"):
            OptimizationReportingRouter(
                (
                    (OptimizationReportFormat.PLAIN_TEXT, plain_text),
                    (OptimizationReportFormat.PLAIN_TEXT, markdown),
                )
            )

    def test_invalid_construction_and_public_exports_are_intentional(self) -> None:
        facade = _RecordingFacade(OptimizationResultRenderedReport("plain"))

        values = (
            None,
            [],
            (("plain_text", facade),),
            ((OptimizationReportFormat.PLAIN_TEXT,),),
        )
        for value in values:
            with self.subTest(value=value), self.assertRaises(TypeError):
                OptimizationReportingRouter(value)  # type: ignore[arg-type]

        from src.engines.backtesting import (
            OptimizationReportFormat as PackageFormat,
            OptimizationReportingRouter as PackageRouter,
        )
        from src.engines.backtesting.reporting import (
            OptimizationReportFormat as ModuleFormat,
            OptimizationReportingRouter as ModuleRouter,
        )

        self.assertIs(PackageFormat, OptimizationReportFormat)
        self.assertIs(ModuleFormat, OptimizationReportFormat)
        self.assertIs(PackageRouter, OptimizationReportingRouter)
        self.assertIs(ModuleRouter, OptimizationReportingRouter)


@dataclass
class _RecordingFacade:
    """Test-only injected facade retaining one exact received completed run."""

    result: OptimizationResultRenderedReport[str]
    received_run: OptimizationRun | None = None
    call_count: int = 0

    def render_run(self, run: OptimizationRun) -> OptimizationResultRenderedReport[str]:
        """Record one exact run and return the configured rendered report."""
        self.received_run = run
        self.call_count += 1
        return self.result


class _SkippedExecutionEngine:
    """Minimal execution dependency for structural completed optimization runs."""

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Return one skipped result without executing a trade."""
        return ExecutionResult(request, ExecutionStatus.SKIPPED)


def _router(
    plain_text: _RecordingFacade,
    markdown: _RecordingFacade,
) -> OptimizationReportingRouter:
    """Build one deterministic fully registered router from injected facades."""
    return OptimizationReportingRouter(
        (
            (OptimizationReportFormat.PLAIN_TEXT, plain_text),
            (OptimizationReportFormat.MARKDOWN, markdown),
        )
    )


def _run() -> OptimizationRun:
    """Build one existing run without executing optimization stages."""
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
