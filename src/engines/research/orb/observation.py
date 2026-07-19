"""Pure objective observations of canonical candles after an ORB escape."""

from datetime import datetime

from src.engines.data.models import Candle, Session
from src.engines.research.orb.escape import find_first_escape_event
from src.engines.research.orb.models import (
    OpeningRange,
    ORBEscapeDirection,
    ORBEscapeEvent,
    ORBPostEscapeObservation,
)

__all__ = ["observe_post_escape"]


def observe_post_escape(
    opening_range: OpeningRange,
    escape_event: ORBEscapeEvent,
    session: Session,
) -> ORBPostEscapeObservation:
    """Observe canonical price facts strictly after the first ORB escape candle.

    A return inside the range occurs when a later candle's observed price
    interval intersects the inclusive opening-range interval. Excursions are
    non-negative distances from the boundary crossed by the escape event.

    Args:
        opening_range: Observed canonical range extracted from ``session``.
        escape_event: The first canonical escape event for ``opening_range``.
        session: Canonical session containing the range and escape event.

    Returns:
        Immutable factual observations from candles strictly after the event.

    Raises:
        TypeError: If an argument is not the required canonical model type.
        ValueError: If the range and event do not belong to ``session``.
    """
    _validate_inputs(opening_range, escape_event, session)

    event_index = session.candles.index(escape_event.candle)
    post_escape_candles = session.candles[event_index + 1 :]
    if not post_escape_candles:
        return ORBPostEscapeObservation(
            highest_price=None,
            lowest_price=None,
            maximum_favorable_excursion=None,
            maximum_adverse_excursion=None,
            returned_inside_range=False,
            first_return_inside_timestamp=None,
        )

    highest_price = max(candle.high for candle in post_escape_candles)
    lowest_price = min(candle.low for candle in post_escape_candles)
    return_timestamp = _first_return_inside_timestamp(post_escape_candles, opening_range)
    favorable, adverse = _excursions(
        escape_event=escape_event,
        highest_price=highest_price,
        lowest_price=lowest_price,
    )

    return ORBPostEscapeObservation(
        highest_price=highest_price,
        lowest_price=lowest_price,
        maximum_favorable_excursion=favorable,
        maximum_adverse_excursion=adverse,
        returned_inside_range=return_timestamp is not None,
        first_return_inside_timestamp=return_timestamp,
    )


def _validate_inputs(
    opening_range: OpeningRange,
    escape_event: ORBEscapeEvent,
    session: Session,
) -> None:
    """Require the supplied event to be the first escape from this session range."""
    if not isinstance(opening_range, OpeningRange):
        raise TypeError("opening_range must be an OpeningRange.")
    if not isinstance(escape_event, ORBEscapeEvent):
        raise TypeError("escape_event must be an ORBEscapeEvent.")
    if not isinstance(session, Session):
        raise TypeError("session must be a Session.")

    expected_event = find_first_escape_event(opening_range, session)
    if expected_event is None or escape_event != expected_event:
        raise ValueError("escape_event does not belong to the supplied session range.")


def _first_return_inside_timestamp(
    candles: tuple[Candle, ...],
    opening_range: OpeningRange,
) -> datetime | None:
    """Return the first timestamp whose observed candle interval intersects range."""
    for candle in candles:
        if candle.low <= opening_range.high and candle.high >= opening_range.low:
            return candle.timestamp
    return None


def _excursions(
    *,
    escape_event: ORBEscapeEvent,
    highest_price: float,
    lowest_price: float,
) -> tuple[float, float]:
    """Measure non-negative post-event distances from the crossed boundary."""
    boundary = escape_event.boundary_crossed
    if escape_event.direction is ORBEscapeDirection.UPWARD:
        return max(0.0, highest_price - boundary), max(0.0, boundary - lowest_price)
    return max(0.0, boundary - lowest_price), max(0.0, highest_price - boundary)
