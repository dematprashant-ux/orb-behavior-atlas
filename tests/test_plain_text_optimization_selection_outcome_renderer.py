"""Contract tests for plain-text rendering of complete selection outcomes."""

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
    OptimizationResultReport,
    OptimizationResultRenderedReport,
    OptimizationRun,
    OptimizationSearchRun,
    OptimizationSelectionOutcomeReport,
    OptimizationSelectionOutcomeReportRenderer,
    OptimizationStrategyMetadata,
    OptimizationTerminationReason,
    PlainTextOptimizationSelectionOutcomeRenderer,
    RankedObjectiveScore,
    StandardObjectiveRanker,
    StandardOptimizationRunner,
    TopRankedSelectionPolicy,
)
from src.engines.execution import ExecutionRequest, ExecutionResult, ExecutionStatus
from src.engines.research import ORBBehaviorAtlas
from src.engines.strategy import CandidateParameterSet, ORBRuleStrategy


class PlainTextOptimizationSelectionOutcomeRendererTests(TestCase):
    """Verify direct plain-text rendering of retained immutable outcomes."""

    def test_renderer_is_stateless_and_satisfies_the_outcome_protocol(self) -> None:
        renderer: OptimizationSelectionOutcomeReportRenderer[str] = (
            PlainTextOptimizationSelectionOutcomeRenderer()
        )

        self.assertTrue(OptimizationSelectionOutcomeReportRenderer._is_protocol)
        self.assertEqual(renderer, PlainTextOptimizationSelectionOutcomeRenderer())
        self.assertEqual(
            repr(renderer),
            repr(PlainTextOptimizationSelectionOutcomeRenderer()),
        )
        self.assertEqual(PlainTextOptimizationSelectionOutcomeRenderer.__slots__, ())

    def test_zero_selection_uses_fixed_plain_text_heading_and_count(self) -> None:
        rendered = PlainTextOptimizationSelectionOutcomeRenderer().render(_outcome(()))

        self.assertIsInstance(rendered, OptimizationResultRenderedReport)
        self.assertEqual(
            rendered.payload,
            "Optimization Selection Outcome\nSelection Count: 0",
        )

    def test_single_and_tied_outcomes_preserve_canonical_order_and_values(self) -> None:
        single = PlainTextOptimizationSelectionOutcomeRenderer().render(
            _outcome(((('orb_minutes', 15),),), selected_count=1)
        )
        tied = PlainTextOptimizationSelectionOutcomeRenderer().render(
            _outcome(
                (
                    (("first", "a|b"), ("note", "line break")),
                    (("second", 2),),
                    (("ignored", 3),),
                ),
                selected_count=2,
            )
        )

        self.assertEqual(
            single.payload,
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
        self.assertEqual(
            tied.payload.split("\n"),
            [
                "Optimization Selection Outcome",
                "Selection Count: 2",
                "Selected Outcome 1:",
                "Rank: 1",
                "Parameters: first=a|b; note=line break",
                "Objective Score: 3.0",
                "Objective Direction: maximize",
                "Selected Outcome 2:",
                "Rank: 2",
                "Parameters: second=2",
                "Objective Score: 2.0",
                "Objective Direction: maximize",
            ],
        )
        self.assertNotIn("ignored=3", tied.payload)

    def test_rendering_is_deterministic_without_other_execution(self) -> None:
        outcome = _outcome(((('first', 1),), (("other", 2),)), selected_count=1)
        renderer = PlainTextOptimizationSelectionOutcomeRenderer()

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
            first = renderer.render(outcome)
            second = renderer.render(outcome)

        self.assertEqual(first, second)
        self.assertFalse(first.payload.startswith("\n"))
        self.assertFalse(first.payload.endswith("\n"))
        self.assertNotIn("| Rank |", first.payload)
        self.assertNotIn("| --- |", first.payload)
        self.assertNotIn("```", first.payload)
        self.assertTrue(
            all(line == line.rstrip() for line in first.payload.split("\n"))
        )

    def test_invalid_input_is_rejected_and_public_export_is_intentional(self) -> None:
        outcome = _outcome(((('first', 1),),), selected_count=1)
        renderer = PlainTextOptimizationSelectionOutcomeRenderer()

        for value in (
            None,
            outcome.result_report,
            outcome.result_report.run,
            outcome.result_report.selection,
            {},
            "outcome",
        ):
            with self.subTest(value=value), self.assertRaisesRegex(TypeError, "report"):
                renderer.render(value)  # type: ignore[arg-type]

        from src.engines.backtesting import (
            PlainTextOptimizationSelectionOutcomeRenderer as PackageRenderer,
        )
        from src.engines.backtesting.reporting import (
            PlainTextOptimizationSelectionOutcomeRenderer as ModuleRenderer,
        )

        self.assertIs(PackageRenderer, PlainTextOptimizationSelectionOutcomeRenderer)
        self.assertIs(ModuleRenderer, PlainTextOptimizationSelectionOutcomeRenderer)


class _SkippedExecutionEngine:
    """Minimal execution dependency for structural candidate outcomes."""

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Return one skipped result without executing a trade."""
        return ExecutionResult(request, ExecutionStatus.SKIPPED)


def _outcome(
    assignments_by_candidate: tuple[tuple[tuple[str, object], ...], ...],
    selected_count: int = 0,
) -> OptimizationSelectionOutcomeReport:
    """Build one existing outcome without executing optimization stages."""
    objective_scores = tuple(
        _objective_score(index, assignments)
        for index, assignments in enumerate(assignments_by_candidate, start=1)
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
    return OptimizationSelectionOutcomeReport.from_result_report(
        OptimizationResultReport.from_run_and_selection(run, selection)
    )


def _objective_score(
    index: int,
    assignments: tuple[tuple[str, object], ...],
) -> ObjectiveScore:
    """Create one completed score fixture without objective evaluation."""
    context = BacktestContext(
        ORBBehaviorAtlas(records=()),
        ORBRuleStrategy(),
        _SkippedExecutionEngine(),
    )
    evaluation = CandidateEvaluation(
        CandidateParameterSet(assignments),
        BacktestRun(context, BacktestStatus.COMPLETED),
    )
    return ObjectiveScore(evaluation, float(4 - index), ObjectiveDirection.MAXIMIZE)
