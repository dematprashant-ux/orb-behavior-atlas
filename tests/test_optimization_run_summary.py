"""Contract tests for read-only immutable optimization run summaries."""

from dataclasses import FrozenInstanceError
from unittest import TestCase

from src.engines.backtesting import (
    BacktestContext,
    BacktestRun,
    BacktestStatus,
    CandidateEvaluation,
    ConstraintDiagnostic,
    ConstraintDiagnostics,
    ConstraintRejection,
    ObjectiveDirection,
    ObjectiveRanking,
    ObjectiveScore,
    ObjectiveSelection,
    OptimizationProgress,
    OptimizationRun,
    OptimizationRunSummary,
    OptimizationSearchRun,
    OptimizationStrategyMetadata,
    OptimizationTerminationReason,
    RankedObjectiveScore,
)
from src.engines.execution import ExecutionRequest, ExecutionResult, ExecutionStatus
from src.engines.research import ORBBehaviorAtlas
from src.engines.strategy import CandidateParameterSet, ORBRuleStrategy


class OptimizationRunSummaryTests(TestCase):
    """Verify summaries only project immutable completed run state."""

    def test_summary_is_immutable_deterministic_and_retains_identity(self) -> None:
        run = _run(
            progress=OptimizationProgress(1, 2),
            termination_reason=OptimizationTerminationReason.EVALUATION_BUDGET_REACHED,
            diagnostics=ConstraintDiagnostics(
                (
                    ConstraintRejection(
                        CandidateParameterSet((("orb_minutes", 30),)),
                        ConstraintDiagnostic("minimum_orb", "too_short"),
                    ),
                )
            ),
        )

        summary = OptimizationRunSummary.from_run(run)

        self.assertEqual(summary, OptimizationRunSummary.from_run(run))
        self.assertEqual(repr(summary), repr(OptimizationRunSummary.from_run(run)))
        self.assertIs(summary.strategy_metadata, run.strategy_metadata)
        self.assertIs(summary.termination_reason, run.termination_reason)
        self.assertEqual(summary.evaluated_candidate_count, 1)
        self.assertEqual(summary.total_eligible_candidate_count, 2)
        self.assertEqual(summary.completion_ratio, 0.5)
        self.assertEqual(summary.rejection_count, 1)
        with self.assertRaises(FrozenInstanceError):
            summary.rejection_count = 0  # type: ignore[misc]

    def test_empty_and_rejected_runs_preserve_progress_semantics(self) -> None:
        all_rejected = _run(
            progress=OptimizationProgress(0, 0),
            termination_reason=OptimizationTerminationReason.SEARCH_SPACE_EXHAUSTED,
            diagnostics=ConstraintDiagnostics(
                (
                    ConstraintRejection(
                        CandidateParameterSet((("orb_minutes", 5),)),
                        ConstraintDiagnostic("minimum_orb", "too_short"),
                    ),
                )
            ),
            evaluations=(),
        )
        empty = _run(
            progress=OptimizationProgress(0, 0),
            termination_reason=OptimizationTerminationReason.SEARCH_SPACE_EXHAUSTED,
            diagnostics=ConstraintDiagnostics(),
            evaluations=(),
        )

        rejected_summary = OptimizationRunSummary.from_run(all_rejected)
        empty_summary = OptimizationRunSummary.from_run(empty)

        self.assertEqual(rejected_summary.rejection_count, 1)
        self.assertEqual(rejected_summary.completion_ratio, 0.0)
        self.assertEqual(empty_summary.rejection_count, 0)
        self.assertEqual(empty_summary.evaluated_candidate_count, 0)
        self.assertEqual(empty_summary.total_eligible_candidate_count, 0)

    def test_summary_rejects_intrinsic_misuse_and_is_exported(self) -> None:
        with self.assertRaisesRegex(TypeError, "run"):
            OptimizationRunSummary.from_run(None)  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "eligible"):
            OptimizationRunSummary(
                OptimizationStrategyMetadata("test"),
                2,
                1,
                0.0,
                OptimizationTerminationReason.SEARCH_SPACE_EXHAUSTED,
                0,
            )

        from src.engines.backtesting import OptimizationRunSummary as PackageSummary

        self.assertIs(PackageSummary, OptimizationRunSummary)


class _SkippedExecutionEngine:
    """Minimal execution collaborator for immutable backtest test artifacts."""

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Return a skipped result without simulating an execution."""
        return ExecutionResult(request, ExecutionStatus.SKIPPED)


def _run(
    *,
    progress: OptimizationProgress,
    termination_reason: OptimizationTerminationReason,
    diagnostics: ConstraintDiagnostics,
    evaluations: tuple[CandidateEvaluation, ...] | None = None,
) -> OptimizationRun:
    """Build one internally consistent completed immutable optimization run."""
    source_evaluations = (_evaluation(),) if evaluations is None else evaluations
    scores = tuple(
        ObjectiveScore(evaluation, 1.0, ObjectiveDirection.MAXIMIZE)
        for evaluation in source_evaluations
    )
    ranking = ObjectiveRanking(
        ObjectiveDirection.MAXIMIZE,
        tuple(
            RankedObjectiveScore(score, index)
            for index, score in enumerate(scores, start=1)
        ),
    )
    selection = ObjectiveSelection(ranking, ranking.ranked_scores[:1])
    search_run = OptimizationSearchRun(
        OptimizationStrategyMetadata("test"),
        source_evaluations,
        progress,
        termination_reason,
        diagnostics,
    )
    return OptimizationRun(search_run, scores, ranking, selection)


def _evaluation() -> CandidateEvaluation:
    """Return one existing immutable evaluation without optimizer execution."""
    context = BacktestContext(
        behavior_atlas=ORBBehaviorAtlas(records=()),
        strategy=ORBRuleStrategy(),
        execution_engine=_SkippedExecutionEngine(),
    )
    return CandidateEvaluation(
        CandidateParameterSet((("orb_minutes", 15),)),
        BacktestRun(context, BacktestStatus.COMPLETED),
    )
