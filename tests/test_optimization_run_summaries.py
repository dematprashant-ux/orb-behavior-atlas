"""Contract tests for immutable ordered optimization summary collections."""

from dataclasses import FrozenInstanceError
from unittest import TestCase

from src.engines.backtesting import (
    OptimizationRunSummaries,
    OptimizationRunSummary,
    OptimizationStrategyMetadata,
    OptimizationTerminationReason,
)


class OptimizationRunSummariesTests(TestCase):
    """Verify collections retain existing summary observations without analysis."""

    def test_empty_collection_is_immutable_and_deterministic(self) -> None:
        first = OptimizationRunSummaries(())
        second = OptimizationRunSummaries(())

        self.assertEqual(first, second)
        self.assertEqual(repr(first), repr(second))
        self.assertEqual(len(first), 0)
        self.assertEqual(tuple(first), ())
        with self.assertRaises(FrozenInstanceError):
            first.summaries = ()  # type: ignore[misc]

    def test_order_identity_and_duplicates_are_preserved(self) -> None:
        first = _summary("first")
        second = _summary("second")
        collection = OptimizationRunSummaries([second, first, second])

        self.assertEqual(tuple(collection), (second, first, second))
        self.assertEqual(len(collection), 3)
        self.assertIs(collection[0], second)
        self.assertIs(collection[1], first)
        self.assertIs(collection[2], second)

    def test_source_mutation_cannot_change_normalized_tuple_storage(self) -> None:
        summaries = [_summary("first")]
        collection = OptimizationRunSummaries(summaries)

        summaries.append(_summary("second"))

        self.assertEqual(len(collection), 1)
        self.assertIs(collection[0], summaries[0])

    def test_invalid_elements_fail_without_a_partial_collection(self) -> None:
        valid = _summary("valid")

        with self.assertRaisesRegex(TypeError, "only"):
            OptimizationRunSummaries((valid, None))  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "iterable"):
            OptimizationRunSummaries(None)  # type: ignore[arg-type]

    def test_public_export_is_intentional(self) -> None:
        from src.engines.backtesting import (
            OptimizationRunSummaries as PackageSummaries,
        )

        self.assertIs(PackageSummaries, OptimizationRunSummaries)


def _summary(name: str) -> OptimizationRunSummary:
    """Return one existing immutable summary without optimization execution."""
    return OptimizationRunSummary(
        OptimizationStrategyMetadata(name),
        1,
        1,
        1.0,
        OptimizationTerminationReason.SEARCH_SPACE_EXHAUSTED,
        0,
    )
