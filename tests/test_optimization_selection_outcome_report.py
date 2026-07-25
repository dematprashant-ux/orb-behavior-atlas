"""Contract tests for complete immutable optimization selection outcomes."""

from dataclasses import FrozenInstanceError
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
    OptimizationRun,
    OptimizationSearchRun,
    OptimizationSelectionOutcomeReport,
    OptimizationStrategyMetadata,
    OptimizationTerminationReason,
    RankedObjectiveScore,
    StandardObjectiveRanker,
    TopRankedSelectionPolicy,
)
from src.engines.execution import ExecutionRequest, ExecutionResult, ExecutionStatus
from src.engines.research import ORBBehaviorAtlas
from src.engines.strategy import CandidateParameterSet, ORBRuleStrategy


class OptimizationSelectionOutcomeReportTests(TestCase):
    """Verify complete canonical selections remain read-only report data."""

    def test_empty_selection_is_retained_by_identity_without_a_winner(self) -> None:
        result_report = _result_report(())

        report = OptimizationSelectionOutcomeReport.from_result_report(result_report)

        self.assertIs(report.result_report, result_report)
        self.assertIs(
            report.selected_outcomes,
            result_report.selection.selected_scores,
        )
        self.assertEqual(report.selection_count, 0)
        self.assertEqual(tuple(report.selected_outcomes), ())
        for name in ("winner", "best", "selected_candidate", "primary_selection"):
            self.assertFalse(hasattr(report, name))

    def test_unique_and_tied_selections_preserve_exact_ordered_identities(self) -> None:
        unique_result_report = _result_report((3.0,), selected_count=1)
        tied_result_report = _result_report((3.0, 3.0, 1.0), selected_count=2)

        unique = OptimizationSelectionOutcomeReport.from_result_report(
            unique_result_report
        )
        tied = OptimizationSelectionOutcomeReport.from_result_report(tied_result_report)

        self.assertEqual(unique.selection_count, 1)
        self.assertIs(
            unique.selected_outcomes[0],
            unique_result_report.selection.selected_scores[0],
        )
        self.assertEqual(tied.selection_count, 2)
        self.assertEqual(
            tied.selected_outcomes,
            tied_result_report.selection.selected_scores,
        )
        for outcome, selected_score in zip(
            tied.selected_outcomes,
            tied_result_report.selection.selected_scores,
        ):
            self.assertIs(outcome, selected_score)

    def test_report_is_immutable_deterministic_and_does_not_execute_stages(
        self,
    ) -> None:
        result_report = _result_report((2.0, 1.0), selected_count=1)

        with patch.object(
            StandardObjectiveRanker,
            "rank",
            side_effect=AssertionError("ranking must not execute"),
        ), patch.object(
            TopRankedSelectionPolicy,
            "select",
            side_effect=AssertionError("selection must not execute"),
        ):
            first = OptimizationSelectionOutcomeReport.from_result_report(
                result_report
            )
            second = OptimizationSelectionOutcomeReport.from_result_report(
                result_report
            )

        self.assertEqual(first, second)
        self.assertEqual(repr(first), repr(second))
        with self.assertRaises(FrozenInstanceError):
            first.result_report = result_report  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            first.selected_outcomes = ()  # type: ignore[misc]

    def test_invalid_input_and_noncanonical_selected_collection_are_rejected(
        self,
    ) -> None:
        result_report = _result_report((1.0,), selected_count=1)
        for value in (
            None,
            result_report.run,
            result_report.selection,
            result_report.selection.ranking,
            result_report.selection.selected_scores[0],
            (),
            {},
            "result_report",
        ):
            with self.subTest(value=value), self.assertRaisesRegex(
                TypeError,
                "result_report",
            ):
                OptimizationSelectionOutcomeReport.from_result_report(
                    value
                )  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "exact collection"):
            OptimizationSelectionOutcomeReport(result_report, ())

    def test_public_export_is_intentional(self) -> None:
        from src.engines.backtesting import (
            OptimizationSelectionOutcomeReport as PackageReport,
        )
        from src.engines.backtesting.summary import (
            OptimizationSelectionOutcomeReport as ModuleReport,
        )

        self.assertIs(PackageReport, OptimizationSelectionOutcomeReport)
        self.assertIs(ModuleReport, OptimizationSelectionOutcomeReport)


class _SkippedExecutionEngine:
    """Minimal execution dependency for structural candidate outcomes."""

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Return one skipped result without executing a trade."""
        return ExecutionResult(request, ExecutionStatus.SKIPPED)


def _result_report(
    scores: tuple[float, ...],
    selected_count: int = 0,
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
    selection = ObjectiveSelection(
        ranking,
        ranking.ranked_scores[:selected_count],
    )
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
    """Create one existing score fixture without scoring execution."""
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
