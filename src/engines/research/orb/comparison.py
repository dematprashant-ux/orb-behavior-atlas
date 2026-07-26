"""Pure descriptive comparison of two immutable ORB behavior atlases."""

from math import isfinite

from src.engines.research.orb.descriptive import (
    compute_behavior_descriptive_statistics,
)
from src.engines.research.orb.models import (
    ORBBehaviorAtlas,
    ORBBehaviorComparison,
    ORBFeatureSummary,
    ORBFeatureSummaryDifference,
)

__all__ = ["compare_behavior_atlases"]


def compare_behavior_atlases(
    left: ORBBehaviorAtlas,
    right: ORBBehaviorAtlas,
) -> ORBBehaviorComparison:
    """Compare two atlas subsets through the canonical descriptive API.

    Categorical counts and proportions remain available on each retained
    descriptive-statistics value. Numeric differences are absolute and only
    exist when both sides have the corresponding observed numeric metric.
    """
    if not isinstance(left, ORBBehaviorAtlas):
        raise TypeError("left must be an ORBBehaviorAtlas.")
    if not isinstance(right, ORBBehaviorAtlas):
        raise TypeError("right must be an ORBBehaviorAtlas.")

    left_statistics = compute_behavior_descriptive_statistics(left)
    right_statistics = compute_behavior_descriptive_statistics(right)
    return ORBBehaviorComparison(
        left_statistics=left_statistics,
        right_statistics=right_statistics,
        range_size_difference=_feature_summary_difference(
            left_statistics.range_size,
            right_statistics.range_size,
        ),
        maximum_favorable_excursion_difference=_feature_summary_difference(
            left_statistics.maximum_favorable_excursion,
            right_statistics.maximum_favorable_excursion,
        ),
        maximum_adverse_excursion_difference=_feature_summary_difference(
            left_statistics.maximum_adverse_excursion,
            right_statistics.maximum_adverse_excursion,
        ),
    )


def _feature_summary_difference(
    left: ORBFeatureSummary,
    right: ORBFeatureSummary,
) -> ORBFeatureSummaryDifference:
    """Calculate absolute differences for existing summary metrics only."""
    return ORBFeatureSummaryDifference(
        count_difference=abs(left.count - right.count),
        minimum_difference=_absolute_difference(left.minimum, right.minimum),
        maximum_difference=_absolute_difference(left.maximum, right.maximum),
        mean_difference=_absolute_difference(left.mean, right.mean),
        median_difference=_absolute_difference(left.median, right.median),
    )


def _absolute_difference(left: float | None, right: float | None) -> float | None:
    """Return an observed absolute difference without fabricating missing data."""
    if left is None or right is None:
        return None
    difference = abs(left - right)
    if not isfinite(difference):
        raise ValueError("feature summary differences must be finite values.")
    return difference
