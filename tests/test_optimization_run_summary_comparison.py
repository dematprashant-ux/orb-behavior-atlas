"""Contract tests for immutable optimization summary comparison composition."""

from dataclasses import FrozenInstanceError
from unittest import TestCase
from unittest.mock import patch

from src.engines.backtesting import (
    OptimizationRunSummaries,
    OptimizationRunSummary,
    OptimizationRunSummaryAnalysis,
    OptimizationRunSummaryComparison,
    OptimizationRunSummaryDelta,
    OptimizationStrategyMetadata,
    OptimizationTerminationReason,
)


class OptimizationRunSummaryComparisonTests(TestCase):
    """Verify comparison retains canonical existing analysis and delta objects."""

    def test_comparison_is_immutable_deterministic_and_retains_identities(
        self,
    ) -> None:
        baseline = _analysis((_summary("grid", 1, 2, 0, _EXHAUSTED),))
        comparison = _analysis((_summary("random", 2, 2, 1, _BUDGET),))

        result = OptimizationRunSummaryComparison.between(baseline, comparison)

        self.assertIs(result.baseline, baseline)
        self.assertIs(result.comparison, comparison)
        self.assertEqual(
            result.delta,
            OptimizationRunSummaryDelta.between(baseline, comparison),
        )
        self.assertEqual(
            result,
            OptimizationRunSummaryComparison.between(baseline, comparison),
        )
        self.assertEqual(
            repr(result),
            repr(OptimizationRunSummaryComparison.between(baseline, comparison)),
        )
        with self.assertRaises(FrozenInstanceError):
            result.baseline = comparison  # type: ignore[misc]

    def test_factory_delegates_once_and_retains_exact_delta_identity(self) -> None:
        baseline = _analysis(())
        comparison = _analysis((_summary("grid", 1, 1, 0, _EXHAUSTED),))
        delta = OptimizationRunSummaryDelta(1, 1, 1, 0, 1, 0, 1.0, 0.0, 1.0, 0.0)

        with patch.object(
            OptimizationRunSummaryDelta,
            "between",
            return_value=delta,
        ) as delta_factory:
            result = OptimizationRunSummaryComparison.between(baseline, comparison)

        delta_factory.assert_called_once_with(baseline, comparison)
        self.assertIs(result.baseline, baseline)
        self.assertIs(result.comparison, comparison)
        self.assertIs(result.delta, delta)

    def test_same_and_empty_analysis_comparisons_are_valid(self) -> None:
        empty = _analysis(())
        populated = _analysis((_summary("grid", 1, 1, 0, _EXHAUSTED),))

        empty_result = OptimizationRunSummaryComparison.between(empty, empty)
        same_result = OptimizationRunSummaryComparison.between(populated, populated)

        self.assertIs(empty_result.baseline, empty)
        self.assertIs(empty_result.comparison, empty)
        self.assertEqual(empty_result.delta, _zero_delta())
        self.assertEqual(same_result.delta, _zero_delta())

    def test_invalid_inputs_and_delta_failure_propagate_without_partial_result(
        self,
    ) -> None:
        baseline = _analysis(())
        comparison = _analysis((_summary("grid", 1, 1, 0, _EXHAUSTED),))

        for value in (None, (), baseline.aggregate, baseline.rates):
            with self.subTest(value=value), self.assertRaisesRegex(
                TypeError,
                "baseline",
            ):
                OptimizationRunSummaryComparison.between(
                    value,
                    comparison,
                )  # type: ignore[arg-type]
            with self.subTest(value=value), self.assertRaisesRegex(
                TypeError,
                "comparison",
            ):
                OptimizationRunSummaryComparison.between(
                    baseline,
                    value,
                )  # type: ignore[arg-type]

        with patch.object(
            OptimizationRunSummaryDelta,
            "between",
            side_effect=RuntimeError("delta failure"),
        ), self.assertRaisesRegex(RuntimeError, "delta failure"):
            OptimizationRunSummaryComparison.between(baseline, comparison)

        self.assertEqual(baseline.aggregate.run_count, 0)
        self.assertEqual(comparison.aggregate.run_count, 1)

    def test_public_export_is_intentional(self) -> None:
        from src.engines.backtesting import (
            OptimizationRunSummaryComparison as PackageComparison,
        )

        self.assertIs(PackageComparison, OptimizationRunSummaryComparison)


_EXHAUSTED = OptimizationTerminationReason.SEARCH_SPACE_EXHAUSTED
_BUDGET = OptimizationTerminationReason.EVALUATION_BUDGET_REACHED


def _summary(
    name: str,
    evaluated_count: int,
    total_eligible_count: int,
    rejection_count: int,
    termination_reason: OptimizationTerminationReason,
) -> OptimizationRunSummary:
    """Return one immutable summary without optimization execution."""
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


def _analysis(
    summaries: tuple[OptimizationRunSummary, ...],
) -> OptimizationRunSummaryAnalysis:
    """Build a canonical analysis from existing summaries."""
    return OptimizationRunSummaryAnalysis.from_summaries(
        OptimizationRunSummaries(summaries)
    )


def _zero_delta() -> OptimizationRunSummaryDelta:
    """Return the exact all-zero directional delta."""
    return OptimizationRunSummaryDelta(0, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0)
