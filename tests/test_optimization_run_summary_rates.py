"""Contract tests for aggregate-only immutable optimization summary rates."""

from dataclasses import FrozenInstanceError
from unittest import TestCase

from src.engines.backtesting import (
    OptimizationRunSummaries,
    OptimizationRunSummary,
    OptimizationRunSummaryAggregate,
    OptimizationRunSummaryRates,
    OptimizationStrategyMetadata,
    OptimizationTerminationReason,
)


class OptimizationRunSummaryRatesTests(TestCase):
    """Verify rates derive only from existing aggregate scalar values."""

    def test_zero_aggregate_produces_immutable_deterministic_zero_rates(self) -> None:
        aggregate = OptimizationRunSummaryAggregate(0, 0, 0, 0, 0, 0)

        first = OptimizationRunSummaryRates.from_aggregate(aggregate)
        second = OptimizationRunSummaryRates.from_aggregate(aggregate)

        self.assertEqual(first, second)
        self.assertEqual(repr(first), repr(second))
        self.assertEqual(
            first,
            OptimizationRunSummaryRates(0.0, 0.0, 0.0, 0.0),
        )
        with self.assertRaises(FrozenInstanceError):
            first.candidate_completion_rate = 1.0  # type: ignore[misc]

    def test_rates_use_existing_aggregate_counts_without_reinterpretation(self) -> None:
        aggregate = OptimizationRunSummaryAggregate(4, 3, 5, 2, 3, 1)

        rates = OptimizationRunSummaryRates.from_aggregate(aggregate)

        self.assertEqual(rates.candidate_completion_rate, 0.6)
        self.assertEqual(rates.recorded_rejection_rate, 0.4)
        self.assertEqual(rates.search_space_exhausted_rate, 0.75)
        self.assertEqual(rates.evaluation_budget_reached_rate, 0.25)
        self.assertIsInstance(rates.candidate_completion_rate, float)
        self.assertEqual(aggregate, OptimizationRunSummaryAggregate(4, 3, 5, 2, 3, 1))

    def test_zero_denominators_are_zero_without_inferencing_candidates(self) -> None:
        aggregate = OptimizationRunSummaryAggregate(1, 0, 0, 0, 1, 0)

        rates = OptimizationRunSummaryRates.from_aggregate(aggregate)

        self.assertEqual(rates.candidate_completion_rate, 0.0)
        self.assertEqual(rates.recorded_rejection_rate, 0.0)
        self.assertEqual(rates.search_space_exhausted_rate, 1.0)
        self.assertEqual(rates.evaluation_budget_reached_rate, 0.0)

    def test_invalid_sources_and_impossible_rate_state_are_rejected(self) -> None:
        with self.assertRaisesRegex(TypeError, "aggregate"):
            OptimizationRunSummaryRates.from_aggregate(None)  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "aggregate"):
            OptimizationRunSummaryRates.from_aggregate({})  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "aggregate"):
            OptimizationRunSummaryRates.from_aggregate(
                _summary()
            )  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "aggregate"):
            OptimizationRunSummaryRates.from_aggregate(
                OptimizationRunSummaries(())
            )  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "numerator"):
            OptimizationRunSummaryRates.from_aggregate(
                OptimizationRunSummaryAggregate(1, 2, 1, 0, 1, 0)
            )

    def test_public_export_is_intentional(self) -> None:
        from src.engines.backtesting import (
            OptimizationRunSummaryRates as PackageRates,
        )

        self.assertIs(PackageRates, OptimizationRunSummaryRates)


def _summary() -> OptimizationRunSummary:
    """Return one summary only to verify unsupported source types are rejected."""
    return OptimizationRunSummary(
        OptimizationStrategyMetadata("test"),
        0,
        0,
        0.0,
        OptimizationTerminationReason.SEARCH_SPACE_EXHAUSTED,
        0,
    )
