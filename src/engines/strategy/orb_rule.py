"""Deterministic non-executing ORB rule strategy over existing research facts."""

from src.engines.research.orb.models import ORBBehaviorKind, ORBEscapeDirection
from src.engines.strategy.models import (
    StrategyContext,
    StrategyDecision,
    StrategyDecisionType,
)

__all__ = ["ORBRuleStrategy"]


class ORBRuleStrategy:
    """Map existing ORB behavior facts to structural setup decision types."""

    def evaluate(self, context: StrategyContext) -> StrategyDecision:
        """Return a deterministic structural decision for an existing context.

        This strategy reads only the completed record's existing behavior kind
        and, when needed, existing escape direction. It does not inspect
        candles, recalculate observations, generate features, execute trades,
        or access infrastructure.

        Args:
            context: Existing immutable research context to evaluate.

        Returns:
            A new immutable structural setup decision referencing ``context``.

        Raises:
            TypeError: If ``context`` is not a ``StrategyContext``.
            ValueError: If existing record facts cannot support the documented
                rule mapping.
        """
        if not isinstance(context, StrategyContext):
            raise TypeError("context must be a StrategyContext.")

        behavior = context.record.behavior.kind
        if behavior in (
            ORBBehaviorKind.NO_ESCAPE,
            ORBBehaviorKind.ESCAPE_WITH_RETURN,
        ):
            return StrategyDecision(
                context=context,
                decision_type=StrategyDecisionType.NO_ACTION,
            )
        if behavior is not ORBBehaviorKind.ESCAPE_WITHOUT_RETURN:
            raise ValueError("context record contains an unsupported behavior kind.")

        escape_event = context.record.escape_event
        if escape_event is None:
            raise ValueError("escape behavior requires an existing escape event.")
        if escape_event.direction is ORBEscapeDirection.UPWARD:
            decision_type = StrategyDecisionType.LONG_SETUP
        elif escape_event.direction is ORBEscapeDirection.DOWNWARD:
            decision_type = StrategyDecisionType.SHORT_SETUP
        else:
            raise ValueError("context record contains an unsupported escape direction.")

        return StrategyDecision(context=context, decision_type=decision_type)
