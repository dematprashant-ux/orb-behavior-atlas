"""Pure construction of the in-memory canonical ORB behavior atlas."""

from collections.abc import Sequence

from src.engines.research.orb.models import ORBBehaviorAtlas, ORBBehaviorRecord

__all__ = ["build_behavior_atlas"]


def build_behavior_atlas(records: Sequence[ORBBehaviorRecord]) -> ORBBehaviorAtlas:
    """Build an ordered immutable atlas from completed behavior records.

    The supplied order is retained exactly. Duplicate records are detected by
    existing ``ORBBehaviorRecord`` value equality; child records are retained by
    reference and are never copied or modified.

    Args:
        records: Ordered completed behavior records for this in-memory atlas.

    Returns:
        An immutable atlas holding the supplied records in the same order.

    Raises:
        TypeError: If ``records`` is not a sequence of behavior records.
        ValueError: If equal records appear more than once.
    """
    if not isinstance(records, Sequence):
        raise TypeError("records must be a sequence of ORBBehaviorRecord instances.")

    atlas_records: tuple[ORBBehaviorRecord, ...] = ()
    for record in records:
        if not isinstance(record, ORBBehaviorRecord):
            raise TypeError("records must contain only ORBBehaviorRecord instances.")
        if record in atlas_records:
            raise ValueError("records must not contain duplicate ORBBehaviorRecord values.")
        atlas_records += (record,)

    return ORBBehaviorAtlas(records=atlas_records)
