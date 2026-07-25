"""Contract tests for scalar immutable optimization summary aggregates."""

from dataclasses import FrozenInstanceError
from unittest import TestCase

from src.engines.backtesting import (
    OptimizationRunSummaries,
    OptimizationRunSummary,
    OptimizationRunSummaryAggregate,
    OptimizationStrategyMetadata,
    OptimizationTerminationReason,
)


class OptimizationRunSummaryAggregateTests(TestCase):
    """Verify aggregate construction consumes only existing summary values."""

    def test_empty_collection_produces_an_immutable_zero_aggregate(self) -> None:
        aggregate = OptimizationRunSummaryAggregate.from_summaries(
            OptimizationRunSummaries(())
        )

        self.assertEqual(
            aggregate,
            OptimizationRunSummaryAggregate(0, 0, 0, 0, 0, 0),
        )
        self.assertEqual(
            repr(aggregate),
            repr(OptimizationRunSummaryAggregate(0, 0, 0, 0, 0, 0)),
        )
        with self.assertRaises(FrozenInstanceError):
            aggregate.run_count = 1  # type: ignore[misc]

    def test_exact_counts_and_duplicate_contributions_are_preserved(self) -> None:
        exhausted = _summary(
            "grid",
            3,
            3,
            2,
            OptimizationTerminationReason.SEARCH_SPACE_EXHAUSTED,
        )
        budgeted = _summary(
            "random",
            1,
            4,
            1,
            OptimizationTerminationReason.EVALUATION_BUDGET_REACHED,
        )
        summaries = OptimizationRunSummaries((exhausted, budgeted, exhausted))

        aggregate = OptimizationRunSummaryAggregate.from_summaries(summaries)

        self.assertEqual(aggregate.run_count, 3)
        self.assertEqual(aggregate.evaluated_candidate_count, 7)
        self.assertEqual(aggregate.total_eligible_candidate_count, 10)
        self.assertEqual(aggregate.recorded_rejection_count, 5)
        self.assertEqual(aggregate.search_space_exhausted_count, 2)
        self.assertEqual(aggregate.evaluation_budget_reached_count, 1)
        self.assertEqual(summaries.summaries, (exhausted, budgeted, exhausted))

    def test_collection_order_does_not_change_scalar_aggregate_equality(self) -> None:
        first = _summary(
            "first",
            1,
            1,
            0,
            OptimizationTerminationReason.SEARCH_SPACE_EXHAUSTED,
        )
        second = _summary(
            "second",
            1,
            2,
            1,
            OptimizationTerminationReason.EVALUATION_BUDGET_REACHED,
        )

        forward = OptimizationRunSummaryAggregate.from_summaries(
            OptimizationRunSummaries((first, second))
        )
        reverse = OptimizationRunSummaryAggregate.from_summaries(
            OptimizationRunSummaries((second, first))
        )

        self.assertEqual(forward, reverse)

    def test_aggregate_rejects_invalid_source_and_intrinsic_totals(self) -> None:
        with self.assertRaisesRegex(TypeError, "summaries"):
            OptimizationRunSummaryAggregate.from_summaries(())  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "termination"):
            OptimizationRunSummaryAggregate(1, 0, 0, 0, 0, 0)
        with self.assertRaisesRegex(TypeError, "run_count"):
            OptimizationRunSummaryAggregate(
                True, 0, 0, 0, 0, 0
            )  # type: ignore[arg-type]

    def test_public_export_is_intentional(self) -> None:
        from src.engines.backtesting import (
            OptimizationRunSummaryAggregate as PackageAggregate,
        )

        self.assertIs(PackageAggregate, OptimizationRunSummaryAggregate)


def _summary(
    name: str,
    evaluated_count: int,
    total_eligible_count: int,
    rejection_count: int,
    termination_reason: OptimizationTerminationReason,
) -> OptimizationRunSummary:
    """Return one existing immutable summary without optimization execution."""
    completion_ratio = (
        0.0 if total_eligible_count == 0 else evaluated_count / total_eligible_count
    )
    return OptimizationRunSummary(
        OptimizationStrategyMetadata(name),
        evaluated_count,
        total_eligible_count,
        completion_ratio,
        termination_reason,
        rejection_count,
    )
