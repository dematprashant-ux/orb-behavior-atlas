"""Deterministic extraction of opening ranges from canonical sessions."""

from datetime import datetime, timedelta

from src.engines.data.models import Candle, Session
from src.engines.research.orb.models import OpeningRange, ORBWindow

__all__ = ["extract_opening_range"]


def extract_opening_range(
    session: Session,
    *,
    duration: timedelta,
) -> OpeningRange:
    """Extract observed opening-range facts from the start of a canonical session.

    The requested interval is start-inclusive and end-exclusive. It must align
    exactly to the session timeframe, and each expected canonical candle must
    be present in the supplied session order.

    Args:
        session: Canonical session whose candles provide the observed facts.
        duration: Positive opening-range duration aligned to the timeframe.

    Returns:
        An immutable opening range containing the exact included candles.

    Raises:
        TypeError: If ``duration`` is not a ``timedelta``.
        ValueError: If the duration is invalid or the session cannot supply the
            complete requested canonical opening window.
    """
    _validate_duration(duration, session)

    if not session.candles:
        raise ValueError("Cannot extract an opening range from an empty session.")

    candle_count = duration // session.timeframe.duration
    if len(session.candles) < candle_count:
        raise ValueError("Requested ORB window exceeds available session candles.")

    included_candles = session.candles[:candle_count]
    start_timestamp = included_candles[0].timestamp
    _require_expected_timestamps(
        included_candles,
        start_timestamp=start_timestamp,
        timeframe_duration=session.timeframe.duration,
    )

    return OpeningRange(
        window=ORBWindow(
            start_timestamp=start_timestamp,
            end_timestamp=start_timestamp + duration,
        ),
        open=included_candles[0].open,
        high=max(candle.high for candle in included_candles),
        low=min(candle.low for candle in included_candles),
        close=included_candles[-1].close,
        candles=included_candles,
    )


def _validate_duration(duration: timedelta, session: Session) -> None:
    """Require a positive duration that represents whole session candles."""
    if not isinstance(duration, timedelta):
        raise TypeError("duration must be a timedelta.")
    if duration <= timedelta():
        raise ValueError("duration must be greater than zero.")
    if duration % session.timeframe.duration:
        raise ValueError("duration must align to the session timeframe.")


def _require_expected_timestamps(
    candles: tuple[Candle, ...],
    *,
    start_timestamp: datetime,
    timeframe_duration: timedelta,
) -> None:
    """Require exactly one canonical candle at each requested window boundary."""
    for index, candle in enumerate(candles):
        expected_timestamp = start_timestamp + (timeframe_duration * index)
        if candle.timestamp != expected_timestamp:
            raise ValueError(
                "Session does not contain the required canonical ORB candle timestamps."
            )
