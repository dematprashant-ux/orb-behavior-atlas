"""Pure construction of immutable Strategy Engine contexts."""

from src.engines.research.orb.models import ORBBehaviorAtlas, ORBBehaviorRecord
from src.engines.strategy.models import StrategyContext

__all__ = ["build_strategy_context"]


def build_strategy_context(
    record: ORBBehaviorRecord,
    atlas: ORBBehaviorAtlas,
) -> StrategyContext:
    """Build a context that references one existing record within its atlas.

    The builder retains the exact supplied objects and performs no market
    analysis, feature generation, trading decision, or infrastructure access.

    Args:
        record: Existing completed research record selected for future strategy
            evaluation.
        atlas: Existing immutable atlas that contains ``record``.

    Returns:
        An immutable context retaining the supplied references.

    Raises:
        TypeError: If either input is not the required research model type.
        ValueError: If ``record`` is not present in ``atlas``.
    """
    if not isinstance(record, ORBBehaviorRecord):
        raise TypeError("record must be an ORBBehaviorRecord.")
    if not isinstance(atlas, ORBBehaviorAtlas):
        raise TypeError("atlas must be an ORBBehaviorAtlas.")
    if record not in atlas:
        raise ValueError("record must be present in atlas.")

    return StrategyContext(record=record, atlas=atlas)
