"""Pure deterministic evaluation of explicit ORB behavior hypotheses."""

from src.engines.research.orb.comparison import compare_behavior_atlases
from src.engines.research.orb.models import (
    ORBBehaviorAtlas,
    ORBBehaviorDescriptiveStatistics,
    ORBBehaviorHypothesis,
    ORBBehaviorHypothesisEvaluation,
    ORBHypothesisMetric,
    ORBHypothesisNotEvaluableReason,
    ORBHypothesisOutcome,
    ORBHypothesisRelation,
)

__all__ = ["evaluate_behavior_hypothesis"]


def evaluate_behavior_hypothesis(
    hypothesis: ORBBehaviorHypothesis,
    left: ORBBehaviorAtlas,
    right: ORBBehaviorAtlas,
) -> ORBBehaviorHypothesisEvaluation:
    """Evaluate one explicit relation using only canonical comparison facts."""
    if not isinstance(hypothesis, ORBBehaviorHypothesis):
        raise TypeError("hypothesis must be an ORBBehaviorHypothesis.")

    comparison = compare_behavior_atlases(left, right)
    left_value = _resolve_observed_value(comparison.left_statistics, hypothesis)
    right_value = _resolve_observed_value(comparison.right_statistics, hypothesis)
    reason = _not_evaluable_reason(left_value, right_value)
    if reason is not None:
        return ORBBehaviorHypothesisEvaluation(
            hypothesis=hypothesis,
            comparison=comparison,
            left_value=left_value,
            right_value=right_value,
            signed_difference=None,
            absolute_difference=None,
            outcome=ORBHypothesisOutcome.NOT_EVALUABLE,
            not_evaluable_reason=reason,
        )

    signed_difference = left_value - right_value
    absolute_difference = abs(signed_difference)
    outcome = (
        ORBHypothesisOutcome.SUPPORTED
        if _relation_is_satisfied(hypothesis, left_value, right_value)
        and absolute_difference >= hypothesis.minimum_absolute_difference
        else ORBHypothesisOutcome.NOT_SUPPORTED
    )
    return ORBBehaviorHypothesisEvaluation(
        hypothesis=hypothesis,
        comparison=comparison,
        left_value=left_value,
        right_value=right_value,
        signed_difference=signed_difference,
        absolute_difference=absolute_difference,
        outcome=outcome,
        not_evaluable_reason=None,
    )


def _resolve_observed_value(
    statistics: ORBBehaviorDescriptiveStatistics,
    hypothesis: ORBBehaviorHypothesis,
) -> float | None:
    """Read one explicitly supported metric without deriving another fact."""
    if hypothesis.metric is ORBHypothesisMetric.RANGE_SIZE_MEAN:
        return statistics.range_size.mean
    if hypothesis.metric is ORBHypothesisMetric.RANGE_SIZE_MEDIAN:
        return statistics.range_size.median
    if hypothesis.metric is ORBHypothesisMetric.MAXIMUM_FAVORABLE_EXCURSION_MEAN:
        return statistics.maximum_favorable_excursion.mean
    if hypothesis.metric is ORBHypothesisMetric.MAXIMUM_FAVORABLE_EXCURSION_MEDIAN:
        return statistics.maximum_favorable_excursion.median
    if hypothesis.metric is ORBHypothesisMetric.MAXIMUM_ADVERSE_EXCURSION_MEAN:
        return statistics.maximum_adverse_excursion.mean
    if hypothesis.metric is ORBHypothesisMetric.MAXIMUM_ADVERSE_EXCURSION_MEDIAN:
        return statistics.maximum_adverse_excursion.median
    if hypothesis.metric is ORBHypothesisMetric.BEHAVIOR_PROPORTION:
        return statistics.behavior_proportions.get(hypothesis.category)
    if hypothesis.metric is ORBHypothesisMetric.ESCAPE_DIRECTION_PROPORTION:
        return statistics.escape_direction_proportions.get(hypothesis.category)
    if hypothesis.metric is ORBHypothesisMetric.RETURN_TO_RANGE_PROPORTION:
        return statistics.return_to_range_proportions.get(hypothesis.category)
    raise ValueError("hypothesis metric is unsupported")


def _not_evaluable_reason(
    left_value: float | None,
    right_value: float | None,
) -> ORBHypothesisNotEvaluableReason | None:
    """Describe canonical observation absence without assigning a replacement."""
    if left_value is None and right_value is None:
        return ORBHypothesisNotEvaluableReason.BOTH_VALUES_UNAVAILABLE
    if left_value is None:
        return ORBHypothesisNotEvaluableReason.LEFT_VALUE_UNAVAILABLE
    if right_value is None:
        return ORBHypothesisNotEvaluableReason.RIGHT_VALUE_UNAVAILABLE
    return None


def _relation_is_satisfied(
    hypothesis: ORBBehaviorHypothesis,
    left_value: float,
    right_value: float,
) -> bool:
    """Apply only the hypothesis's explicit deterministic directional relation."""
    if hypothesis.relation is ORBHypothesisRelation.GREATER_THAN:
        return left_value > right_value
    if hypothesis.relation is ORBHypothesisRelation.GREATER_THAN_OR_EQUAL:
        return left_value >= right_value
    if hypothesis.relation is ORBHypothesisRelation.LESS_THAN:
        return left_value < right_value
    if hypothesis.relation is ORBHypothesisRelation.LESS_THAN_OR_EQUAL:
        return left_value <= right_value
    if hypothesis.relation is ORBHypothesisRelation.EQUAL:
        return left_value == right_value
    raise ValueError("hypothesis relation is unsupported")
