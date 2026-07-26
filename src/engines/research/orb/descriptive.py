"""Pure descriptive statistics over existing immutable ORB behavior facts."""

from collections.abc import Iterable, Mapping
from math import isfinite

from src.engines.research.orb.distributions import compute_behavior_distributions
from src.engines.research.orb.models import (
    ORBBehaviorAtlas,
    ORBBehaviorDescriptiveStatistics,
    ORBFeatureSummary,
)
from src.engines.research.orb.statistics import compute_behavior_statistics

__all__ = ["compute_behavior_descriptive_statistics"]


def compute_behavior_descriptive_statistics(
    atlas: ORBBehaviorAtlas,
) -> ORBBehaviorDescriptiveStatistics:
    """Summarize existing categorical and numeric facts without market analysis.

    Categorical mappings retain the deterministic first-observed category order
    produced by existing atlas grouping and distribution operations. Empty
    categorical samples have empty mappings. MFE and MAE summaries include
    only existing non-``None`` observations; their empty summaries use count
    zero and ``None`` for every numeric metric.
    """
    if not isinstance(atlas, ORBBehaviorAtlas):
        raise TypeError("atlas must be an ORBBehaviorAtlas.")

    counts = compute_behavior_statistics(atlas)
    distributions = compute_behavior_distributions(atlas)
    return ORBBehaviorDescriptiveStatistics(
        categorical_counts=counts,
        categorical_distributions=distributions,
        behavior_proportions=_proportions(
            distributions.behavior_distribution,
            counts.total_records,
        ),
        escape_direction_proportions=_proportions(
            distributions.escape_direction_distribution,
            counts.upward_escape_count + counts.downward_escape_count,
        ),
        return_to_range_proportions=_proportions(
            distributions.return_to_range_distribution,
            sum(distributions.return_to_range_distribution.values()),
        ),
        range_size=_feature_summary(record.features.range_size for record in atlas),
        maximum_favorable_excursion=_feature_summary(
            record.features.mfe for record in atlas
        ),
        maximum_adverse_excursion=_feature_summary(
            record.features.mae for record in atlas
        ),
    )


def _proportions(
    counts: Mapping[object, int],
    denominator: int,
) -> dict[object, float]:
    """Derive unrounded proportions from an explicit non-negative denominator."""
    if type(denominator) is not int or denominator < 0:
        raise ValueError("denominator must be a non-negative integer.")
    if denominator == 0:
        return {}
    return {category: count / denominator for category, count in counts.items()}


def _feature_summary(values: Iterable[float | None]) -> ORBFeatureSummary:
    """Retain missing observations as absent and reject invalid numeric facts."""
    observed: list[float] = []
    for value in values:
        if value is None:
            continue
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not isfinite(value)
        ):
            raise ValueError("numeric feature observations must be finite values.")
        observed.append(value)

    if not observed:
        return ORBFeatureSummary(0, None, None, None, None)

    ordered = sorted(observed)
    count = len(ordered)
    midpoint = count // 2
    median = (
        ordered[midpoint]
        if count % 2
        else (ordered[midpoint - 1] + ordered[midpoint]) / 2
    )
    return ORBFeatureSummary(
        count=count,
        minimum=ordered[0],
        maximum=ordered[-1],
        mean=sum(ordered) / count,
        median=median,
    )
