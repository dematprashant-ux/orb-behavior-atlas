"""Pure detection of the first observed canonical ORB escape event."""

from src.engines.data.models import Session
from src.engines.research.orb.models import (
    OpeningRange,
    ORBEscapeDirection,
    ORBEscapeEvent,
)

__all__ = ["find_first_escape_event"]


def find_first_escape_event(
    opening_range: OpeningRange,
    session: Session,
) -> ORBEscapeEvent | None:
    """Return the first candle after an opening range that exits its boundaries.

    An upward escape has a high strictly above the observed range high. A
    downward escape has a low strictly below the observed range low. Equality is
    boundary contact, not an escape. A candle crossing both boundaries cannot
    be represented by this single-direction event and is rejected explicitly.

    Args:
        opening_range: Observed canonical range extracted from ``session``.
        session: Canonical session to search after the range window.

    Returns:
        The first immutable observed escape event, or ``None`` when no escape
        candle exists.

    Raises:
        TypeError: If an argument is not the required canonical model type.
        ValueError: If the range does not belong to the session or a single
            candle crosses both range boundaries.
    """
    _validate_range_belongs_to_session(opening_range, session)

    for candle in session.candles[len(opening_range.candles) :]:
        if candle.timestamp < opening_range.window.end_timestamp:
            continue

        crossed_high = candle.high > opening_range.high
        crossed_low = candle.low < opening_range.low
        if crossed_high and crossed_low:
            raise ValueError(
                "A candle crossing both ORB boundaries cannot form a singular escape event."
            )
        if crossed_high:
            return ORBEscapeEvent(
                timestamp=candle.timestamp,
                direction=ORBEscapeDirection.UPWARD,
                candle=candle,
                boundary_crossed=opening_range.high,
                crossing_price=candle.high,
            )
        if crossed_low:
            return ORBEscapeEvent(
                timestamp=candle.timestamp,
                direction=ORBEscapeDirection.DOWNWARD,
                candle=candle,
                boundary_crossed=opening_range.low,
                crossing_price=candle.low,
            )

    return None


def _validate_range_belongs_to_session(
    opening_range: OpeningRange,
    session: Session,
) -> None:
    """Require a complete, canonical opening-range aggregate from this session."""
    if not isinstance(opening_range, OpeningRange):
        raise TypeError("opening_range must be an OpeningRange.")
    if not isinstance(session, Session):
        raise TypeError("session must be a Session.")
    if not opening_range.candles:
        raise ValueError("opening_range must contain at least one candle.")

    candle_count = len(opening_range.candles)
    if session.candles[:candle_count] != opening_range.candles:
        raise ValueError("opening_range does not belong to the supplied session.")

    first_candle = opening_range.candles[0]
    last_candle = opening_range.candles[-1]
    expected_end = first_candle.timestamp + (session.timeframe.duration * candle_count)
    if (
        opening_range.window.start_timestamp != first_candle.timestamp
        or opening_range.window.end_timestamp != expected_end
    ):
        raise ValueError("opening_range window does not match its canonical candles.")

    if (
        opening_range.open != first_candle.open
        or opening_range.high != max(candle.high for candle in opening_range.candles)
        or opening_range.low != min(candle.low for candle in opening_range.candles)
        or opening_range.close != last_candle.close
    ):
        raise ValueError("opening_range values do not match its canonical candles.")
