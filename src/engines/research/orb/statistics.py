"""Pure aggregate statistics over completed immutable ORB behavior records."""

from src.engines.research.orb.models import (
    ORBBehaviorAtlas,
    ORBBehaviorKind,
    ORBBehaviorStatistics,
    ORBEscapeDirection,
)

__all__ = ["compute_behavior_statistics"]


def compute_behavior_statistics(atlas: ORBBehaviorAtlas) -> ORBBehaviorStatistics:
    """Compute supported aggregate counts from existing behavior-record facts.

    The function reads only completed records held by ``atlas``. It does not
    scan candles, classify behavior, generate features, mutate records, cache
    results, or access infrastructure.

    Args:
        atlas: Immutable atlas containing completed ORB behavior records.

    Returns:
        An immutable count-only statistical summary.

    Raises:
        TypeError: If ``atlas`` is not an ``ORBBehaviorAtlas``.
        ValueError: If an atlas record has an unsupported existing behavior or
            escape direction.
    """
    if not isinstance(atlas, ORBBehaviorAtlas):
        raise TypeError("atlas must be an ORBBehaviorAtlas.")

    total_records = 0
    no_escape_count = 0
    escape_with_return_count = 0
    escape_without_return_count = 0
    upward_escape_count = 0
    downward_escape_count = 0
    returned_to_range_count = 0

    for record in atlas:
        total_records += 1
        if record.behavior.kind is ORBBehaviorKind.NO_ESCAPE:
            no_escape_count += 1
        elif record.behavior.kind is ORBBehaviorKind.ESCAPE_WITH_RETURN:
            escape_with_return_count += 1
        elif record.behavior.kind is ORBBehaviorKind.ESCAPE_WITHOUT_RETURN:
            escape_without_return_count += 1
        else:
            raise ValueError("atlas contains an unsupported ORB behavior kind.")

        if record.escape_event is not None:
            if record.escape_event.direction is ORBEscapeDirection.UPWARD:
                upward_escape_count += 1
            elif record.escape_event.direction is ORBEscapeDirection.DOWNWARD:
                downward_escape_count += 1
            else:
                raise ValueError("atlas contains an unsupported escape direction.")

        if (
            record.post_escape_observation is not None
            and record.post_escape_observation.returned_inside_range
        ):
            returned_to_range_count += 1

    return ORBBehaviorStatistics(
        total_records=total_records,
        no_escape_count=no_escape_count,
        escape_with_return_count=escape_with_return_count,
        escape_without_return_count=escape_without_return_count,
        upward_escape_count=upward_escape_count,
        downward_escape_count=downward_escape_count,
        returned_to_range_count=returned_to_range_count,
    )
