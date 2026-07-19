"""Pure immutable categorical distributions over completed ORB behavior atlases."""

from src.engines.research.orb.grouping import (
    group_by_behavior,
    group_by_escape_direction,
    group_by_return_to_range,
)
from src.engines.research.orb.models import (
    ORBBehaviorAtlas,
    ORBBehaviorDistributions,
)

__all__ = ["compute_behavior_distributions"]


def compute_behavior_distributions(
    atlas: ORBBehaviorAtlas,
) -> ORBBehaviorDistributions:
    """Compute observed categorical frequency maps from an immutable atlas.

    Existing grouping operations define the category membership and preserve the
    canonical record boundary. This function uses only resulting group sizes;
    it does not inspect candles, classify behavior, mutate records, normalize
    counts, or access infrastructure.

    Args:
        atlas: Immutable completed behavior records to summarize.

    Returns:
        An immutable observed-category frequency summary.

    Raises:
        TypeError: If ``atlas`` is not an ``ORBBehaviorAtlas``.
    """
    if not isinstance(atlas, ORBBehaviorAtlas):
        raise TypeError("atlas must be an ORBBehaviorAtlas.")

    behavior_groups = group_by_behavior(atlas)
    escape_direction_groups = group_by_escape_direction(atlas)
    return_to_range_groups = group_by_return_to_range(atlas)

    return ORBBehaviorDistributions(
        behavior_distribution={
            category: len(group)
            for category, group in behavior_groups.groups.items()
        },
        escape_direction_distribution={
            category: len(group)
            for category, group in escape_direction_groups.groups.items()
        },
        return_to_range_distribution={
            category: len(group)
            for category, group in return_to_range_groups.groups.items()
        },
    )
