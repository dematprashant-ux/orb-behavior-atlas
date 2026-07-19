"""Pure standardized ORB feature generation from existing research outputs."""

from src.engines.research.orb.models import (
    OpeningRange,
    ORBBehavior,
    ORBBehaviorKind,
    ORBEscapeEvent,
    ORBFeatures,
    ORBPostEscapeObservation,
)

__all__ = ["generate_orb_features"]


def generate_orb_features(
    opening_range: OpeningRange,
    escape_event: ORBEscapeEvent | None,
    post_escape_observation: ORBPostEscapeObservation | None,
    behavior: ORBBehavior,
) -> ORBFeatures:
    """Project existing immutable ORB outputs into standardized feature values.

    ``range_size`` is the direct difference of the stored opening-range bounds.
    No candle is read or scanned, and all other feature values are projections
    of the supplied event, observation, and behavior.

    Args:
        opening_range: Existing immutable opening-range context.
        escape_event: Existing first escape event, or ``None``.
        post_escape_observation: Existing post-escape facts, or ``None``.
        behavior: Existing classification for the supplied optional facts.

    Returns:
        An immutable standardized feature record.

    Raises:
        TypeError: If any input is not the expected immutable model type.
        ValueError: If the optional inputs disagree with the supplied behavior.
    """
    _validate_inputs(opening_range, escape_event, post_escape_observation, behavior)

    if escape_event is None:
        return ORBFeatures(
            behavior=behavior.kind,
            escape_exists=False,
            escape_direction=None,
            returned_to_range=None,
            mfe=None,
            mae=None,
            range_size=opening_range.high - opening_range.low,
        )

    if post_escape_observation is None:
        raise ValueError("an escape event requires a post-escape observation.")

    return ORBFeatures(
        behavior=behavior.kind,
        escape_exists=True,
        escape_direction=escape_event.direction,
        returned_to_range=post_escape_observation.returned_inside_range,
        mfe=post_escape_observation.maximum_favorable_excursion,
        mae=post_escape_observation.maximum_adverse_excursion,
        range_size=opening_range.high - opening_range.low,
    )


def _validate_inputs(
    opening_range: OpeningRange,
    escape_event: ORBEscapeEvent | None,
    post_escape_observation: ORBPostEscapeObservation | None,
    behavior: ORBBehavior,
) -> None:
    """Require optional facts and supplied classification to agree exactly."""
    if not isinstance(opening_range, OpeningRange):
        raise TypeError("opening_range must be an OpeningRange.")
    if escape_event is not None and not isinstance(escape_event, ORBEscapeEvent):
        raise TypeError("escape_event must be an ORBEscapeEvent or None.")
    if post_escape_observation is not None and not isinstance(
        post_escape_observation,
        ORBPostEscapeObservation,
    ):
        raise TypeError(
            "post_escape_observation must be an ORBPostEscapeObservation or None."
        )
    if not isinstance(behavior, ORBBehavior):
        raise TypeError("behavior must be an ORBBehavior.")
    if escape_event is None:
        if post_escape_observation is not None or behavior.kind is not ORBBehaviorKind.NO_ESCAPE:
            raise ValueError("no escape requires no observation and NO_ESCAPE behavior.")
        return

    if post_escape_observation is None:
        raise ValueError("an escape event requires a post-escape observation.")
    expected_behavior = (
        ORBBehaviorKind.ESCAPE_WITH_RETURN
        if post_escape_observation.returned_inside_range
        else ORBBehaviorKind.ESCAPE_WITHOUT_RETURN
    )
    if behavior.kind is not expected_behavior:
        raise ValueError("behavior must match the supplied escape return fact.")
