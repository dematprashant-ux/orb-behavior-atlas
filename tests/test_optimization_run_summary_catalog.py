"""Contract tests for immutable optimization summary comparison catalogs."""

from dataclasses import FrozenInstanceError
from unittest import TestCase

from src.engines.backtesting import (
    OptimizationRunSummaries,
    OptimizationRunSummary,
    OptimizationRunSummaryAnalysis,
    OptimizationRunSummaryCatalog,
    OptimizationRunSummaryComparison,
    OptimizationStrategyMetadata,
    OptimizationTerminationReason,
)


class OptimizationRunSummaryCatalogTests(TestCase):
    """Verify catalogs retain supplied comparison objects unchanged and ordered."""

    def test_empty_catalog_is_immutable_and_deterministic(self) -> None:
        first = OptimizationRunSummaryCatalog(())
        second = OptimizationRunSummaryCatalog(())

        self.assertEqual(len(first), 0)
        self.assertEqual(tuple(first), ())
        self.assertEqual(first, second)
        self.assertEqual(repr(first), repr(second))
        with self.assertRaises(FrozenInstanceError):
            first.comparisons = ()  # type: ignore[misc]

    def test_catalog_preserves_insertion_order_duplicates_and_identity(self) -> None:
        first = _comparison("first", "second")
        second = _comparison("third", "fourth")

        catalog = OptimizationRunSummaryCatalog((second, first, second))

        self.assertEqual(tuple(catalog), (second, first, second))
        self.assertIs(catalog[0], second)
        self.assertIs(catalog[1], first)
        self.assertIs(catalog[2], second)
        self.assertEqual(
            catalog,
            OptimizationRunSummaryCatalog((second, first, second)),
        )

    def test_catalog_normalizes_source_iterables_without_mutating_children(
        self,
    ) -> None:
        first = _comparison("first", "second")
        second = _comparison("third", "fourth")
        source = [first]

        catalog = OptimizationRunSummaryCatalog(source)
        source.append(second)

        self.assertEqual(tuple(catalog), (first,))
        self.assertIs(catalog[0], first)
        self.assertEqual(first.baseline.aggregate.run_count, 1)
        self.assertEqual(second.comparison.aggregate.run_count, 1)

    def test_invalid_elements_fail_without_partial_catalog(self) -> None:
        comparison = _comparison("first", "second")

        with self.assertRaisesRegex(TypeError, "comparisons"):
            OptimizationRunSummaryCatalog(None)  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "comparisons"):
            OptimizationRunSummaryCatalog(
                (comparison, None)
            )  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "comparisons"):
            OptimizationRunSummaryCatalog(
                (comparison, object())
            )  # type: ignore[arg-type]

        self.assertEqual(comparison.baseline.aggregate.run_count, 1)
        self.assertEqual(comparison.delta.run_count_delta, 0)

    def test_public_export_is_intentional(self) -> None:
        from src.engines.backtesting import (
            OptimizationRunSummaryCatalog as PackageCatalog,
        )

        self.assertIs(PackageCatalog, OptimizationRunSummaryCatalog)


_EXHAUSTED = OptimizationTerminationReason.SEARCH_SPACE_EXHAUSTED


def _comparison(
    baseline_name: str,
    comparison_name: str,
) -> OptimizationRunSummaryComparison:
    """Build one existing immutable comparison without optimization execution."""
    baseline = _analysis(baseline_name)
    comparison = _analysis(comparison_name)
    return OptimizationRunSummaryComparison.between(baseline, comparison)


def _analysis(name: str) -> OptimizationRunSummaryAnalysis:
    """Build one canonical analysis from a single existing summary."""
    summary = OptimizationRunSummary(
        OptimizationStrategyMetadata(name),
        1,
        1,
        1.0,
        _EXHAUSTED,
        0,
    )
    return OptimizationRunSummaryAnalysis.from_summaries(
        OptimizationRunSummaries((summary,))
    )
