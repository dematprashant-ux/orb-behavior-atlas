"""Contract tests for directional immutable optimization summary deltas."""

from dataclasses import FrozenInstanceError
from unittest import TestCase
from unittest.mock import patch

from src.engines.backtesting import (
    OptimizationRunSummaries,
    OptimizationRunSummary,
    OptimizationRunSummaryAnalysis,
    OptimizationRunSummaryDelta,
    OptimizationStrategyMetadata,
    OptimizationTerminationReason,
)


class OptimizationRunSummaryDeltaTests(TestCase):
    """Verify deltas read only retained analysis scalar values directionally."""

    def test_same_and_empty_analyses_produce_immutable_zero_deltas(self) -> None:
        analysis = _analysis((_summary("grid", 2, 4, 1, _EXHAUSTED),))
        empty = _analysis(())

        same_delta = OptimizationRunSummaryDelta.between(analysis, analysis)
        empty_delta = OptimizationRunSummaryDelta.between(empty, empty)

        self.assertEqual(same_delta, _zero_delta())
        self.assertEqual(empty_delta, _zero_delta())
        self.assertEqual(repr(same_delta), repr(empty_delta))
        with self.assertRaises(FrozenInstanceError):
            same_delta.run_count_delta = 1  # type: ignore[misc]

    def test_all_count_and_rate_deltas_are_comparison_minus_baseline(self) -> None:
        baseline = _analysis(
            (
                _summary("grid", 2, 4, 1, _EXHAUSTED),
                _summary("random", 1, 4, 0, _BUDGET),
            )
        )
        comparison = _analysis(
            (
                _summary("grid", 3, 3, 0, _EXHAUSTED),
                _summary("random", 2, 2, 2, _EXHAUSTED),
                _summary("grid", 0, 2, 1, _BUDGET),
            )
        )

        delta = OptimizationRunSummaryDelta.between(baseline, comparison)

        self.assertEqual(delta.run_count_delta, 1)
        self.assertEqual(delta.evaluated_candidate_count_delta, 2)
        self.assertEqual(delta.total_eligible_candidate_count_delta, -1)
        self.assertEqual(delta.recorded_rejection_count_delta, 2)
        self.assertEqual(delta.search_space_exhausted_count_delta, 1)
        self.assertEqual(delta.evaluation_budget_reached_count_delta, 0)
        self.assertEqual(
            delta.candidate_completion_rate_delta,
            (
                comparison.rates.candidate_completion_rate
                - baseline.rates.candidate_completion_rate
            ),
        )
        self.assertEqual(
            delta.recorded_rejection_rate_delta,
            (
                comparison.rates.recorded_rejection_rate
                - baseline.rates.recorded_rejection_rate
            ),
        )
        self.assertEqual(
            delta.search_space_exhausted_rate_delta,
            (
                comparison.rates.search_space_exhausted_rate
                - baseline.rates.search_space_exhausted_rate
            ),
        )
        self.assertEqual(
            delta.evaluation_budget_reached_rate_delta,
            (
                comparison.rates.evaluation_budget_reached_rate
                - baseline.rates.evaluation_budget_reached_rate
            ),
        )
        self.assertEqual(baseline.aggregate.run_count, 2)
        self.assertEqual(comparison.aggregate.run_count, 3)

    def test_swapping_analyses_negates_every_signed_delta(self) -> None:
        baseline = _analysis((_summary("grid", 1, 2, 1, _EXHAUSTED),))
        comparison = _analysis((_summary("random", 1, 4, 0, _BUDGET),))

        forward = OptimizationRunSummaryDelta.between(baseline, comparison)
        reverse = OptimizationRunSummaryDelta.between(comparison, baseline)

        for name in _COUNT_FIELD_NAMES:
            self.assertEqual(getattr(reverse, name), -getattr(forward, name))
        for name in _RATE_FIELD_NAMES:
            self.assertAlmostEqual(getattr(reverse, name), -getattr(forward, name))

    def test_between_does_not_traverse_summary_collections(self) -> None:
        baseline = _analysis((_summary("grid", 1, 1, 0, _EXHAUSTED),))
        comparison = _analysis((_summary("random", 1, 1, 0, _BUDGET),))

        with patch.object(
            OptimizationRunSummaries,
            "__iter__",
            side_effect=AssertionError("summaries must not be traversed"),
        ):
            delta = OptimizationRunSummaryDelta.between(baseline, comparison)

        self.assertEqual(delta.run_count_delta, 0)

    def test_between_rejects_non_analysis_inputs_and_is_exported(self) -> None:
        analysis = _analysis(())

        for value in (None, (), analysis.aggregate, analysis.rates, analysis.summaries):
            with self.subTest(value=value), self.assertRaisesRegex(
                TypeError,
                "baseline",
            ):
                OptimizationRunSummaryDelta.between(
                    value,
                    analysis,
                )  # type: ignore[arg-type]
            with self.subTest(value=value), self.assertRaisesRegex(
                TypeError,
                "comparison",
            ):
                OptimizationRunSummaryDelta.between(
                    analysis,
                    value,
                )  # type: ignore[arg-type]

        from src.engines.backtesting import OptimizationRunSummaryDelta as PackageDelta

        self.assertIs(PackageDelta, OptimizationRunSummaryDelta)


_EXHAUSTED = OptimizationTerminationReason.SEARCH_SPACE_EXHAUSTED
_BUDGET = OptimizationTerminationReason.EVALUATION_BUDGET_REACHED
_COUNT_FIELD_NAMES = (
    "run_count_delta",
    "evaluated_candidate_count_delta",
    "total_eligible_candidate_count_delta",
    "recorded_rejection_count_delta",
    "search_space_exhausted_count_delta",
    "evaluation_budget_reached_count_delta",
)
_RATE_FIELD_NAMES = (
    "candidate_completion_rate_delta",
    "recorded_rejection_rate_delta",
    "search_space_exhausted_rate_delta",
    "evaluation_budget_reached_rate_delta",
)


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
    """Return the exact all-zero scalar delta value."""
    return OptimizationRunSummaryDelta(0, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0)
