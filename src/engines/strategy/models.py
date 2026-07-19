"""Immutable structural domain models for the Strategy Engine."""

from dataclasses import dataclass
from enum import Enum

from src.engines.research.orb.models import ORBBehaviorAtlas, ORBBehaviorRecord

__all__ = [
    "StrategyContext",
    "StrategyDecision",
    "StrategyDecisionType",
]


class StrategyDecisionType(str, Enum):
    """Identifies the structural decision states available to future strategies."""

    NO_ACTION = "NO_ACTION"
    LONG_SETUP = "LONG_SETUP"
    SHORT_SETUP = "SHORT_SETUP"


@dataclass(frozen=True, slots=True)
class StrategyContext:
    """References one selected behavior record and its existing research atlas."""

    record: ORBBehaviorRecord
    atlas: ORBBehaviorAtlas


@dataclass(frozen=True, slots=True)
class StrategyDecision:
    """References a strategy context and one structural decision placeholder."""

    context: StrategyContext
    decision_type: StrategyDecisionType

    def __post_init__(self) -> None:
        """Require only the model types intrinsic to a structural decision."""
        if not isinstance(self.context, StrategyContext):
            raise TypeError("context must be a StrategyContext.")
        if not isinstance(self.decision_type, StrategyDecisionType):
            raise TypeError("decision_type must be a StrategyDecisionType.")
