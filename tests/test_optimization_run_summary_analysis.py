"""Contract tests for immutable canonical optimization summary analysis."""

from dataclasses import FrozenInstanceError
from unittest import TestCase
from unittest.mock import patch

from src.engines.backtesting import (
    OptimizationRunSummaries,
    OptimizationRunSummary,
    OptimizationRunSummaryAggregate,
    OptimizationRunSummaryAnalysis,
    OptimizationRunSummaryRates,
    OptimizationStrategyMetadata,
    OptimizationTerminationReason,
)


class OptimizationRunSummaryAnalysisTests(TestCase):
    """Verify analysis composes only canonical existing summary projections."""

    def test_analysis_is_immutable_and_retains_canonical_identities(self) -> None:
        summaries = OptimizationRunSummaries((_summary("grid"), _summary("random")))

        analysis = OptimizationRunSummaryAnalysis.from_summaries(summaries)

        self.assertIs(analysis.summaries, summaries)
        self.assertEqual(
            analysis.aggregate,
            OptimizationRunSummaryAggregate.from_summaries(summaries),
        )
        self.assertEqual(
            analysis.rates,
            OptimizationRunSummaryRates.from_aggregate(analysis.aggregate),
        )
        self.assertEqual(
            analysis,
            OptimizationRunSummaryAnalysis.from_summaries(summaries),
        )
        self.assertEqual(
            repr(analysis),
            repr(OptimizationRunSummaryAnalysis.from_summaries(summaries)),
        )
        with self.assertRaises(FrozenInstanceError):
            analysis.summaries = summaries  # type: ignore[misc]

    def test_factory_retains_exact_canonical_component_identities(self) -> None:
        summaries = OptimizationRunSummaries((_summary("grid"),))
        aggregate = OptimizationRunSummaryAggregate(1, 1, 1, 0, 1, 0)
        rates = OptimizationRunSummaryRates(1.0, 0.0, 1.0, 0.0)

        with patch.object(
            OptimizationRunSummaryAggregate,
            "from_summaries",
            return_value=aggregate,
        ) as aggregate_factory, patch.object(
            OptimizationRunSummaryRates,
            "from_aggregate",
            return_value=rates,
        ) as rates_factory:
            analysis = OptimizationRunSummaryAnalysis.from_summaries(summaries)

        aggregate_factory.assert_called_once_with(summaries)
        rates_factory.assert_called_once_with(aggregate)
        self.assertIs(analysis.summaries, summaries)
        self.assertIs(analysis.aggregate, aggregate)
        self.assertIs(analysis.rates, rates)

    def test_empty_and_duplicate_summaries_retain_existing_semantics(self) -> None:
        empty_summaries = OptimizationRunSummaries(())
        duplicate = _summary("grid")
        duplicate_summaries = OptimizationRunSummaries((duplicate, duplicate))

        empty_analysis = OptimizationRunSummaryAnalysis.from_summaries(empty_summaries)
        duplicate_analysis = OptimizationRunSummaryAnalysis.from_summaries(
            duplicate_summaries
        )

        self.assertIs(empty_analysis.summaries, empty_summaries)
        self.assertEqual(empty_analysis.aggregate.run_count, 0)
        self.assertEqual(empty_analysis.rates.candidate_completion_rate, 0.0)
        self.assertIs(duplicate_analysis.summaries[0], duplicate)
        self.assertIs(duplicate_analysis.summaries[1], duplicate)
        self.assertEqual(duplicate_analysis.aggregate.run_count, 2)

    def test_invalid_input_and_factory_failures_propagate_without_partial_output(
        self,
    ) -> None:
        summaries = OptimizationRunSummaries((_summary("grid"),))

        with self.assertRaisesRegex(TypeError, "summaries"):
            OptimizationRunSummaryAnalysis.from_summaries(
                None
            )  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "summaries"):
            OptimizationRunSummaryAnalysis.from_summaries(())  # type: ignore[arg-type]
        with patch.object(
            OptimizationRunSummaryAggregate,
            "from_summaries",
            side_effect=RuntimeError("aggregate failure"),
        ), self.assertRaisesRegex(RuntimeError, "aggregate failure"), patch.object(
            OptimizationRunSummaryRates,
            "from_aggregate",
        ) as rates_factory:
            OptimizationRunSummaryAnalysis.from_summaries(summaries)
        rates_factory.assert_not_called()

        aggregate = OptimizationRunSummaryAggregate(1, 1, 1, 0, 1, 0)
        with patch.object(
            OptimizationRunSummaryAggregate,
            "from_summaries",
            return_value=aggregate,
        ), patch.object(
            OptimizationRunSummaryRates,
            "from_aggregate",
            side_effect=RuntimeError("rates failure"),
        ), self.assertRaisesRegex(RuntimeError, "rates failure"):
            OptimizationRunSummaryAnalysis.from_summaries(summaries)
        self.assertIs(summaries[0], summaries.summaries[0])

    def test_public_export_is_intentional(self) -> None:
        from src.engines.backtesting import (
            OptimizationRunSummaryAnalysis as PackageAnalysis,
        )

        self.assertIs(PackageAnalysis, OptimizationRunSummaryAnalysis)


def _summary(name: str) -> OptimizationRunSummary:
    """Return one immutable summary without executing any optimization stage."""
    return OptimizationRunSummary(
        OptimizationStrategyMetadata(name),
        1,
        1,
        1.0,
        OptimizationTerminationReason.SEARCH_SPACE_EXHAUSTED,
        0,
    )
