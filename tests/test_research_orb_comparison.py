"""Contract tests for deterministic comparison of immutable ORB atlases."""

from dataclasses import FrozenInstanceError, is_dataclass
from unittest import TestCase
from unittest.mock import patch

from src.engines.research import (
    ORBBehaviorComparison,
    ORBBehaviorKind,
    ORBEscapeDirection,
    ORBFeatureSummaryDifference,
    build_behavior_atlas,
    compare_behavior_atlases,
    compute_behavior_descriptive_statistics,
)
from tests.test_research_orb_descriptive_statistics import (
    _escape_record,
    _no_escape_record,
)


class ORBBehaviorComparisonTests(TestCase):
    """Verify comparison composes existing statistics without new analysis."""

    def test_empty_atlases_retain_existing_empty_statistics(self) -> None:
        """Compare no records without fabricating categories or numeric values."""
        comparison = compare_behavior_atlases(
            build_behavior_atlas(()),
            build_behavior_atlas(()),
        )

        self.assertIsInstance(comparison, ORBBehaviorComparison)
        self.assertEqual(comparison.left_statistics.categorical_counts.total_records, 0)
        self.assertEqual(comparison.right_statistics.categorical_counts.total_records, 0)
        self.assertEqual(
            comparison.range_size_difference,
            ORBFeatureSummaryDifference(0, None, None, None, None),
        )

    def test_populated_and_empty_atlases_preserve_missing_numeric_semantics(self) -> None:
        """Keep categorical facts and absent numeric comparisons explicit."""
        populated = build_behavior_atlas((_no_escape_record(range_size=4.0),))
        comparison = compare_behavior_atlases(populated, build_behavior_atlas(()))

        self.assertEqual(
            dict(comparison.left_statistics.behavior_proportions),
            {ORBBehaviorKind.NO_ESCAPE: 1.0},
        )
        self.assertEqual(comparison.right_statistics.categorical_counts.total_records, 0)
        self.assertEqual(
            comparison.range_size_difference,
            ORBFeatureSummaryDifference(1, None, None, None, None),
        )

    def test_identical_atlases_have_zero_existing_numeric_differences(self) -> None:
        """Describe equal summaries without changing the supplied atlas records."""
        record = _escape_record(
            range_size=4.0,
            direction=ORBEscapeDirection.UPWARD,
            returned=True,
            mfe=2.0,
            mae=1.0,
        )
        atlas = build_behavior_atlas((record,))

        comparison = compare_behavior_atlases(atlas, atlas)

        self.assertEqual(
            comparison.range_size_difference,
            ORBFeatureSummaryDifference(0, 0.0, 0.0, 0.0, 0.0),
        )
        self.assertEqual(
            comparison.maximum_favorable_excursion_difference,
            ORBFeatureSummaryDifference(0, 0.0, 0.0, 0.0, 0.0),
        )
        self.assertEqual(tuple(atlas), (record,))

    def test_different_atlases_expose_canonical_categories_and_absolute_differences(
        self,
    ) -> None:
        """Retain both categorical summaries and compare only stored metrics."""
        left = build_behavior_atlas(
            (
                _no_escape_record(range_size=2.0),
                _escape_record(
                    range_size=4.0,
                    direction=ORBEscapeDirection.UPWARD,
                    returned=True,
                    mfe=1.0,
                    mae=2.0,
                ),
            )
        )
        right = build_behavior_atlas(
            (
                _escape_record(
                    range_size=8.0,
                    direction=ORBEscapeDirection.DOWNWARD,
                    returned=False,
                    mfe=5.0,
                    mae=6.0,
                ),
            )
        )

        comparison = compare_behavior_atlases(left, right)

        self.assertEqual(
            dict(comparison.left_statistics.categorical_distributions.behavior_distribution),
            {
                ORBBehaviorKind.NO_ESCAPE: 1,
                ORBBehaviorKind.ESCAPE_WITH_RETURN: 1,
            },
        )
        self.assertEqual(
            dict(comparison.right_statistics.escape_direction_proportions),
            {ORBEscapeDirection.DOWNWARD: 1.0},
        )
        self.assertEqual(
            comparison.range_size_difference,
            ORBFeatureSummaryDifference(1, 6.0, 4.0, 5.0, 5.0),
        )
        self.assertEqual(
            comparison.maximum_adverse_excursion_difference,
            ORBFeatureSummaryDifference(0, 4.0, 4.0, 4.0, 4.0),
        )

    def test_filtered_atlases_preserve_existing_group_order(self) -> None:
        """Compare pre-filtered immutable subsets without adding query behavior."""
        upward = _escape_record(
            range_size=3.0,
            direction=ORBEscapeDirection.UPWARD,
            returned=False,
            mfe=1.0,
            mae=2.0,
        )
        downward = _escape_record(
            range_size=6.0,
            direction=ORBEscapeDirection.DOWNWARD,
            returned=True,
            mfe=2.0,
            mae=1.0,
        )
        atlas = build_behavior_atlas((downward, upward))

        comparison = compare_behavior_atlases(
            atlas.filter(escape_direction=ORBEscapeDirection.DOWNWARD),
            atlas.filter(escape_direction=ORBEscapeDirection.UPWARD),
        )

        self.assertEqual(
            tuple(comparison.left_statistics.escape_direction_proportions),
            (ORBEscapeDirection.DOWNWARD,),
        )
        self.assertEqual(
            tuple(comparison.right_statistics.escape_direction_proportions),
            (ORBEscapeDirection.UPWARD,),
        )
        self.assertEqual(tuple(atlas), (downward, upward))

    def test_reuses_descriptive_statistics_once_for_each_input(self) -> None:
        """Delegate both sides to the existing canonical descriptive function."""
        left = build_behavior_atlas((_no_escape_record(range_size=2.0),))
        right = build_behavior_atlas((_no_escape_record(range_size=4.0),))

        with patch(
            "src.engines.research.orb.comparison."
            "compute_behavior_descriptive_statistics",
            wraps=compute_behavior_descriptive_statistics,
        ) as descriptive:
            compare_behavior_atlases(left, right)

        self.assertEqual(descriptive.call_count, 2)
        self.assertEqual(descriptive.call_args_list[0].args, (left,))
        self.assertEqual(descriptive.call_args_list[1].args, (right,))

    def test_result_is_deterministic_and_immutable(self) -> None:
        """Return equal frozen comparison values across repeated execution."""
        atlas = build_behavior_atlas((_no_escape_record(range_size=2.0),))

        first = compare_behavior_atlases(atlas, build_behavior_atlas(()))
        second = compare_behavior_atlases(atlas, build_behavior_atlas(()))

        self.assertEqual(first, second)
        self.assertTrue(is_dataclass(first))
        self.assertFalse(hasattr(first, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            first.left_statistics = second.left_statistics

    def test_rejects_non_atlas_inputs_and_exports_public_types(self) -> None:
        """Keep the immutable atlas boundary and intended exports explicit."""
        with self.assertRaises(TypeError):
            compare_behavior_atlases((), build_behavior_atlas(()))
        with self.assertRaises(TypeError):
            compare_behavior_atlases(build_behavior_atlas(()), ())

        from src.engines.research import ORBBehaviorComparison as PackageComparison
        from src.engines.research import (
            ORBFeatureSummaryDifference as PackageFeatureDifference,
        )

        self.assertIs(PackageComparison, ORBBehaviorComparison)
        self.assertIs(PackageFeatureDifference, ORBFeatureSummaryDifference)
