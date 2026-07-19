"""Pure classification of ORB behavior from existing immutable observations."""

from src.engines.research.orb.models import (
    OpeningRange,
    ORBBehavior,
    ORBBehaviorKind,
    ORBEscapeEvent,
    ORBPostEscapeObservation,
)

__all__ = ["classify_orb_behavior"]


def classify_orb_behavior(
    opening_range: OpeningRange,
    escape_event: ORBEscapeEvent | None,
    post_escape_observation: ORBPostEscapeObservation | None,
) -> ORBBehavior:
    """Classify only the ORB behavior states supported by supplied observations.

    The classifier does not read candles or derive market facts. A missing
    escape event represents ``NO_ESCAPE`` only when no post-escape observation
    is supplied. An escape event requires its corresponding observation.

    Args:
        opening_range: Existing immutable range context for the classification.
        escape_event: First observed escape, or ``None`` when no escape exists.
        post_escape_observation: Existing facts after ``escape_event``, if any.

    Returns:
        An immutable objective behavior classification.

    Raises:
        TypeError: If any supplied value has an unsupported model type.
        ValueError: If the optional inputs form an impossible classification
            state.
    """
    _validate_inputs(opening_range, escape_event, post_escape_observation)

    if escape_event is None:
        return ORBBehavior(kind=ORBBehaviorKind.NO_ESCAPE)
    if post_escape_observation.returned_inside_range:
        return ORBBehavior(kind=ORBBehaviorKind.ESCAPE_WITH_RETURN)
    return ORBBehavior(kind=ORBBehaviorKind.ESCAPE_WITHOUT_RETURN)


def _validate_inputs(
    opening_range: OpeningRange,
    escape_event: ORBEscapeEvent | None,
    post_escape_observation: ORBPostEscapeObservation | None,
) -> None:
    """Require only the model relationships needed by the pure mapping."""
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
    if escape_event is None and post_escape_observation is not None:
        raise ValueError("a post-escape observation requires an escape event.")
    if escape_event is not None and post_escape_observation is None:
        raise ValueError("an escape event requires a post-escape observation.")
