"""Pure immutable grouping of completed ORB behavior atlas records."""

from src.engines.research.orb.models import (
    ORBBehaviorAtlas,
    ORBBehaviorAtlasGroups,
    ORBBehaviorKind,
    ORBBehaviorRecord,
    ORBEscapeDirection,
)

__all__ = [
    "group_by_behavior",
    "group_by_escape_direction",
    "group_by_return_to_range",
]


def group_by_behavior(atlas: ORBBehaviorAtlas) -> ORBBehaviorAtlasGroups:
    """Group records by their existing behavior kind.

    Args:
        atlas: Completed immutable records to organize.

    Returns:
        Immutable non-empty groups in first-observed key order.

    Raises:
        TypeError: If ``atlas`` is not an ``ORBBehaviorAtlas``.
    """
    _require_atlas(atlas)
    records_by_behavior: dict[ORBBehaviorKind, list[ORBBehaviorRecord]] = {}
    for record in atlas:
        records_by_behavior.setdefault(record.behavior.kind, []).append(record)
    return _groups_from_records(records_by_behavior)


def group_by_escape_direction(atlas: ORBBehaviorAtlas) -> ORBBehaviorAtlasGroups:
    """Group escaped records by their existing escape direction.

    Records without an escape event have no direction and are omitted.

    Args:
        atlas: Completed immutable records to organize.

    Returns:
        Immutable non-empty groups in first-observed key order.

    Raises:
        TypeError: If ``atlas`` is not an ``ORBBehaviorAtlas``.
    """
    _require_atlas(atlas)
    records_by_direction: dict[ORBEscapeDirection, list[ORBBehaviorRecord]] = {}
    for record in atlas:
        if record.escape_event is not None:
            records_by_direction.setdefault(
                record.escape_event.direction,
                [],
            ).append(record)
    return _groups_from_records(records_by_direction)


def group_by_return_to_range(atlas: ORBBehaviorAtlas) -> ORBBehaviorAtlasGroups:
    """Group escaped records by their existing return-to-range fact.

    Records without a post-escape observation have no return fact and are
    omitted.

    Args:
        atlas: Completed immutable records to organize.

    Returns:
        Immutable non-empty groups in first-observed key order.

    Raises:
        TypeError: If ``atlas`` is not an ``ORBBehaviorAtlas``.
    """
    _require_atlas(atlas)
    records_by_return: dict[bool, list[ORBBehaviorRecord]] = {}
    for record in atlas:
        if record.post_escape_observation is not None:
            returned = record.post_escape_observation.returned_inside_range
            records_by_return.setdefault(returned, []).append(record)
    return _groups_from_records(records_by_return)


def _require_atlas(atlas: ORBBehaviorAtlas) -> None:
    """Require the immutable atlas boundary as the sole grouping input."""
    if not isinstance(atlas, ORBBehaviorAtlas):
        raise TypeError("atlas must be an ORBBehaviorAtlas.")


def _groups_from_records(
    records_by_key: dict[
        ORBBehaviorKind | ORBEscapeDirection | bool,
        list[ORBBehaviorRecord],
    ],
) -> ORBBehaviorAtlasGroups:
    """Create immutable atlas groups without copying any child record object."""
    return ORBBehaviorAtlasGroups(
        groups={
            key: ORBBehaviorAtlas(records=tuple(records))
            for key, records in records_by_key.items()
        }
    )
