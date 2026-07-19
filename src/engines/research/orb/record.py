"""Pure construction of canonical aggregate ORB behavior records."""

from src.engines.research.orb.models import (
    OpeningRange,
    ORBBehavior,
    ORBBehaviorKind,
    ORBBehaviorRecord,
    ORBEscapeDirection,
    ORBEscapeEvent,
    ORBFeatures,
    ORBPostEscapeObservation,
)

__all__ = ["build_behavior_record"]


def build_behavior_record(
    opening_range: OpeningRange,
    escape_event: ORBEscapeEvent | None,
    post_escape_observation: ORBPostEscapeObservation | None,
    behavior: ORBBehavior,
    features: ORBFeatures,
) -> ORBBehaviorRecord:
    """Assemble existing, consistent ORB outputs into one immutable record.

    The factory only compares supplied child-object facts for intrinsic
    consistency. It does not access candles, recompute observations, classify
    behavior, generate features, or perform I/O.
    """
    _validate_inputs(
        opening_range,
        escape_event,
        post_escape_observation,
        behavior,
        features,
    )
    return ORBBehaviorRecord(
        opening_range=opening_range,
        escape_event=escape_event,
        post_escape_observation=post_escape_observation,
        behavior=behavior,
        features=features,
    )


def _validate_inputs(
    opening_range: OpeningRange,
    escape_event: ORBEscapeEvent | None,
    post_escape_observation: ORBPostEscapeObservation | None,
    behavior: ORBBehavior,
    features: ORBFeatures,
) -> None:
    """Require existing child facts to describe the same aggregate record."""
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
    if not isinstance(features, ORBFeatures):
        raise TypeError("features must be an ORBFeatures.")
    if behavior.kind is not features.behavior:
        raise ValueError("behavior and features must use the same behavior kind.")

    if escape_event is None:
        _validate_no_escape_record(post_escape_observation, behavior, features)
        return

    _validate_escape_record(
        opening_range,
        escape_event,
        post_escape_observation,
        behavior,
        features,
    )


def _validate_no_escape_record(
    post_escape_observation: ORBPostEscapeObservation | None,
    behavior: ORBBehavior,
    features: ORBFeatures,
) -> None:
    """Require all supplied values to consistently represent no escape."""
    if (
        post_escape_observation is not None
        or behavior.kind is not ORBBehaviorKind.NO_ESCAPE
        or features.escape_exists
    ):
        raise ValueError("a no-escape record requires no observation and no-escape facts.")


def _validate_escape_record(
    opening_range: OpeningRange,
    escape_event: ORBEscapeEvent,
    post_escape_observation: ORBPostEscapeObservation | None,
    behavior: ORBBehavior,
    features: ORBFeatures,
) -> None:
    """Require existing event, observation, behavior, and feature facts to agree."""
    if post_escape_observation is None:
        raise ValueError("an escape record requires a post-escape observation.")
    if not features.escape_exists or features.escape_direction is not escape_event.direction:
        raise ValueError("escape event and features must use the same escape facts.")

    expected_boundary = (
        opening_range.high
        if escape_event.direction is ORBEscapeDirection.UPWARD
        else opening_range.low
    )
    if escape_event.boundary_crossed != expected_boundary:
        raise ValueError("escape event boundary does not match the opening range.")
    if (
        features.returned_to_range != post_escape_observation.returned_inside_range
        or features.mfe != post_escape_observation.maximum_favorable_excursion
        or features.mae != post_escape_observation.maximum_adverse_excursion
    ):
        raise ValueError("post-escape observation and features must use the same facts.")
    if (
        post_escape_observation.first_return_inside_timestamp is not None
        and post_escape_observation.first_return_inside_timestamp <= escape_event.timestamp
    ):
        raise ValueError("post-escape return timestamp must follow the escape event.")
    if behavior.kind is ORBBehaviorKind.NO_ESCAPE:
        raise ValueError("an escape record cannot use NO_ESCAPE behavior.")
