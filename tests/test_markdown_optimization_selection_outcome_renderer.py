"""Contract tests for Markdown rendering of complete selection outcomes."""

from dataclasses import FrozenInstanceError
from unittest import TestCase
from unittest.mock import patch

from src.engines.backtesting import (
    BacktestContext,
    BacktestRun,
    BacktestStatus,
    CandidateEvaluation,
    ConstraintDiagnostics,
    MarkdownOptimizationSelectionOutcomeRenderer,
    ObjectiveDirection,
    ObjectiveRanking,
    ObjectiveScore,
    ObjectiveSelection,
    OptimizationProgress,
    OptimizationResultReport,
    OptimizationRun,
    OptimizationSearchRun,
    OptimizationSelectionOutcomeReport,
    OptimizationSelectionOutcomeReportRenderer,
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


class MarkdownOptimizationSelectionOutcomeRendererTests(TestCase):
    """Verify deterministic direct rendering of selected immutable outcomes."""

    def test_renderer_is_stateless_and_satisfies_the_outcome_protocol(self) -> None:
        renderer: OptimizationSelectionOutcomeReportRenderer[str] = (
            MarkdownOptimizationSelectionOutcomeRenderer()
        )

        self.assertTrue(OptimizationSelectionOutcomeReportRenderer._is_protocol)
        self.assertEqual(renderer, MarkdownOptimizationSelectionOutcomeRenderer())
        self.assertEqual(
            repr(renderer),
            repr(MarkdownOptimizationSelectionOutcomeRenderer()),
        )
        self.assertEqual(MarkdownOptimizationSelectionOutcomeRenderer.__slots__, ())

    def test_zero_selection_uses_the_fixed_heading_sections_and_empty_table(
        self,
    ) -> None:
        rendered = MarkdownOptimizationSelectionOutcomeRenderer().render(_outcome(()))

        self.assertEqual(
            rendered.payload,
            "\n".join(
                (
                    "# Optimization Selection Outcome",
                    "",
                    "## Summary",
                    "",
                    "Selection Count: 0",
                    "",
                    "## Selected Outcomes",
                    "",
                    "| Rank | Parameters | Objective Score | Direction |",
                    "| --- | --- | --- | --- |",
                )
            ),
        )

    def test_unique_and_tied_outcomes_preserve_canonical_order_and_raw_values(
        self,
    ) -> None:
        unique = MarkdownOptimizationSelectionOutcomeRenderer().render(
            _outcome(((("orb_minutes", 15),),), selected_count=1)
        )
        tied_report = _outcome(
            (
                (("first", "a|b"), ("note", "line\nbreak")),
                (("second", 2),),
                (("ignored", 3),),
            ),
            selected_count=2,
        )
        tied = MarkdownOptimizationSelectionOutcomeRenderer().render(tied_report)

        self.assertIn("Selection Count: 1", unique.payload)
        self.assertIn("| 1 | orb_minutes=15 | 3.0 | maximize |", unique.payload)
        self.assertEqual(
            tied.payload.split("\n")[-2:],
            [
                "| 1 | first=a\\|b; note=line\\nbreak | 3.0 | maximize |",
                "| 2 | second=2 | 2.0 | maximize |",
            ],
        )
        self.assertNotIn("ignored=3", tied.payload)

    def test_rendering_is_deterministic_and_does_not_execute_other_stages(self) -> None:
        outcome = _outcome(((("first", 1),), (("other", 2),)), selected_count=1)
        renderer = MarkdownOptimizationSelectionOutcomeRenderer()

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
        self.assertIs(
            outcome.result_report.selection,
            outcome.result_report.run.selection,
        )
        self.assertIs(
            outcome.selected_outcomes[0],
            outcome.result_report.selection.selected_scores[0],
        )
        self.assertFalse(first.payload.startswith("\n"))
        self.assertFalse(first.payload.endswith("\n"))
        self.assertNotIn("\t", first.payload)
        self.assertNotIn("<", first.payload)
        self.assertNotIn("```", first.payload)
        self.assertTrue(
            all(line == line.rstrip() for line in first.payload.split("\n"))
        )

    def test_invalid_input_is_rejected_without_mutating_source_outcomes(self) -> None:
        outcome = _outcome(((("first", 1),),), selected_count=1)
        renderer = MarkdownOptimizationSelectionOutcomeRenderer()

        for value in (
            None,
            outcome.result_report,
            outcome.result_report.run,
            outcome.result_report.selection,
            outcome.result_report.selection.ranking,
            {},
            "outcome",
        ):
            with self.subTest(value=value), self.assertRaisesRegex(TypeError, "report"):
                renderer.render(value)  # type: ignore[arg-type]
        self.assertEqual(outcome.selection_count, 1)
        with self.assertRaises(FrozenInstanceError):
            outcome.selected_outcomes = ()  # type: ignore[misc]

    def test_public_export_is_intentional(self) -> None:
        from src.engines.backtesting import (
            MarkdownOptimizationSelectionOutcomeRenderer as PackageRenderer,
        )
        from src.engines.backtesting.reporting import (
            MarkdownOptimizationSelectionOutcomeRenderer as ModuleRenderer,
        )

        self.assertIs(PackageRenderer, MarkdownOptimizationSelectionOutcomeRenderer)
        self.assertIs(ModuleRenderer, MarkdownOptimizationSelectionOutcomeRenderer)


class _SkippedExecutionEngine:
    """Minimal execution dependency for structural candidate outcomes."""

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Return one skipped result without executing a trade."""
        return ExecutionResult(request, ExecutionStatus.SKIPPED)


def _outcome(
    assignments_by_candidate: tuple[tuple[tuple[str, object], ...], ...],
    selected_count: int = 0,
) -> OptimizationSelectionOutcomeReport:
    """Build an existing immutable outcome without executing optimization stages."""
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
    result_report = OptimizationResultReport.from_run_and_selection(run, selection)
    return OptimizationSelectionOutcomeReport.from_result_report(result_report)


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
