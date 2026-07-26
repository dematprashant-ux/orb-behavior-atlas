"""Contract tests for composing optimization selection-outcome reporting paths."""

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
    OptimizationProgress,
    OptimizationReportFormat,
    OptimizationReportingCompositionRoot,
    OptimizationReportingRouter,
    OptimizationRun,
    OptimizationSearchRun,
    OptimizationStrategyMetadata,
    OptimizationTerminationReason,
    RankedObjectiveScore,
)
from src.engines.execution import ExecutionRequest, ExecutionResult, ExecutionStatus
from src.engines.research import ORBBehaviorAtlas
from src.engines.strategy import CandidateParameterSet, ORBRuleStrategy


class OptimizationReportingCompositionRootTests(TestCase):
    """Verify composition creates both complete paths without reporting side effects."""

    def test_build_router_assembles_both_formats_with_the_exact_selector(self) -> None:
        selector = _RecordingSelector()
        root = OptimizationReportingCompositionRoot(selector)

        router = root.build_router()

        self.assertIsInstance(router, OptimizationReportingRouter)
        registrations = dict(router.registrations)
        self.assertEqual(
            tuple(registrations),
            (OptimizationReportFormat.PLAIN_TEXT, OptimizationReportFormat.MARKDOWN),
        )
        for facade in registrations.values():
            self.assertIs(facade.reporting_service.selection_policy, selector)
        self.assertEqual(selector.call_count, 0)
        self.assertIsInstance(router.registrations, tuple)

    def test_format_paths_render_their_own_canonical_output_once(self) -> None:
        selector = _RecordingSelector()
        router = OptimizationReportingCompositionRoot(selector).build_router()
        run = _run()

        plain_text = router.render_run(run, OptimizationReportFormat.PLAIN_TEXT)
        markdown = router.render_run(run, OptimizationReportFormat.MARKDOWN)

        self.assertEqual(selector.call_count, 2)
        self.assertEqual(selector.received_rankings, (run.ranking, run.ranking))
        self.assertEqual(
            plain_text.payload,
            "\n".join(
                (
                    "Optimization Selection Outcome",
                    "Selection Count: 1",
                    "Selected Outcome 1:",
                    "Rank: 1",
                    "Parameters: orb_minutes=15",
                    "Objective Score: 3.0",
                    "Objective Direction: maximize",
                )
            ),
        )
        self.assertIn(
            "| Rank | Parameters | Objective Score | Direction |",
            markdown.payload,
        )
        self.assertIn(
            "| 1 | orb_minutes=15 | 3.0 | maximize |",
            markdown.payload,
        )

    def test_composition_is_immutable_and_deterministic(self) -> None:
        selector = _RecordingSelector()
        root = OptimizationReportingCompositionRoot(selector)

        first = root.build_router()
        second = root.build_router()

        self.assertEqual(first, second)
        self.assertEqual(repr(first), repr(second))
        self.assertEqual(selector.call_count, 0)
        with self.assertRaises(FrozenInstanceError):
            root.selection_policy = selector  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            first.registrations = ()  # type: ignore[misc]

    def test_invalid_selector_and_public_export_are_intentional(self) -> None:
        with self.assertRaisesRegex(TypeError, "selection_policy"):
            OptimizationReportingCompositionRoot(None)  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "selection_policy"):
            OptimizationReportingCompositionRoot(object())  # type: ignore[arg-type]

        from src.engines.backtesting import (
            OptimizationReportingCompositionRoot as PackageRoot,
        )
        from src.engines.backtesting.reporting import (
            OptimizationReportingCompositionRoot as ModuleRoot,
        )

        self.assertIs(PackageRoot, OptimizationReportingCompositionRoot)
        self.assertIs(ModuleRoot, OptimizationReportingCompositionRoot)


@dataclass
class _RecordingSelector:
    """Test-only selector retaining each exact ranking received at runtime."""

    received_rankings: tuple[ObjectiveRanking, ...] = ()
    call_count: int = 0

    def select(self, ranking: ObjectiveRanking) -> ObjectiveSelection:
        """Return the canonical first-ranked selection without reranking."""
        self.received_rankings += (ranking,)
        self.call_count += 1
        return ObjectiveSelection(ranking, ranking.ranked_scores[:1])


class _SkippedExecutionEngine:
    """Minimal execution dependency for structural completed optimization runs."""

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Return one skipped result without executing a trade."""
        return ExecutionResult(request, ExecutionStatus.SKIPPED)


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
