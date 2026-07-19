"""Contract tests for first observed canonical ORB escape events."""

from dataclasses import FrozenInstanceError, is_dataclass
from datetime import date, datetime, timedelta
from unittest import TestCase
from zoneinfo import ZoneInfo

from src.engines.data.models import Candle, Instrument, Session, Timeframe, Weekday
from src.engines.research import (
    ORBEscapeDirection,
    ORBEscapeEvent,
    extract_opening_range,
    find_first_escape_event,
)


class ORBEscapeEventTests(TestCase):
    """Verify first-escape discovery remains pure, deterministic, and factual."""

    def test_finds_an_upward_escape(self) -> None:
        """Record the first post-range candle whose high exceeds the ORB high."""
        session = _session(
            _range_candles()
            + (_candle(9, 30, high=107.0, low=103.0, close=106.0),)
        )
        opening_range = extract_opening_range(session, duration=timedelta(minutes=15))

        event = find_first_escape_event(opening_range, session)

        self.assertIsInstance(event, ORBEscapeEvent)
        self.assertEqual(event.timestamp, _timestamp(9, 30))
        self.assertIs(event.candle, session.candles[3])
        self.assertIs(event.direction, ORBEscapeDirection.UPWARD)
        self.assertEqual(event.boundary_crossed, opening_range.high)
        self.assertEqual(event.crossing_price, 107.0)

    def test_finds_a_downward_escape(self) -> None:
        """Record the first post-range candle whose low falls below the ORB low."""
        session = _session(
            _range_candles()
            + (_candle(9, 30, high=105.0, low=97.0, close=98.0),)
        )
        opening_range = extract_opening_range(session, duration=timedelta(minutes=15))

        event = find_first_escape_event(opening_range, session)

        self.assertEqual(event.direction, ORBEscapeDirection.DOWNWARD)
        self.assertEqual(event.boundary_crossed, opening_range.low)
        self.assertEqual(event.crossing_price, 97.0)

    def test_returns_none_when_no_post_range_candle_exits_a_boundary(self) -> None:
        """Treat equality with a range boundary as contact rather than escape."""
        session = _session(
            _range_candles()
            + (_candle(9, 30, high=106.0, low=98.0, close=102.0),)
        )
        opening_range = extract_opening_range(session, duration=timedelta(minutes=15))

        self.assertIsNone(find_first_escape_event(opening_range, session))

    def test_returns_only_the_first_escape_event(self) -> None:
        """Stop at the earliest post-range candle that exits either boundary."""
        session = _session(
            _range_candles()
            + (
                _candle(9, 30, high=107.0, low=103.0, close=106.0),
                _candle(9, 35, high=104.0, low=97.0, close=98.0),
            )
        )
        opening_range = extract_opening_range(session, duration=timedelta(minutes=15))

        event = find_first_escape_event(opening_range, session)

        self.assertEqual(event.timestamp, _timestamp(9, 30))
        self.assertIs(event.direction, ORBEscapeDirection.UPWARD)

    def test_repeated_execution_is_deterministic_and_event_is_immutable(self) -> None:
        """Return equal immutable values without mutating canonical input objects."""
        session = _session(
            _range_candles()
            + (_candle(9, 30, high=107.0, low=103.0, close=106.0),)
        )
        opening_range = extract_opening_range(session, duration=timedelta(minutes=15))

        first = find_first_escape_event(opening_range, session)
        second = find_first_escape_event(opening_range, session)

        self.assertEqual(first, second)
        self.assertTrue(is_dataclass(first))
        self.assertFalse(hasattr(first, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            first.boundary_crossed = 0.0

    def test_escape_direction_values_are_stable(self) -> None:
        """Expose only the two directional states supported by this event model."""
        self.assertEqual(
            tuple(ORBEscapeDirection),
            (ORBEscapeDirection.UPWARD, ORBEscapeDirection.DOWNWARD),
        )

    def test_rejects_an_opening_range_that_does_not_belong_to_the_session(self) -> None:
        """Do not search a session using range evidence from another session."""
        opening_range = extract_opening_range(
            _session(_range_candles()),
            duration=timedelta(minutes=15),
        )
        other_session = _session(
            (
                _candle(9, 15, open_price=99.0),
                _candle(9, 20),
                _candle(9, 25),
            )
        )

        with self.assertRaisesRegex(ValueError, "does not belong"):
            find_first_escape_event(opening_range, other_session)

    def test_rejects_a_candle_crossing_both_boundaries(self) -> None:
        """Avoid inventing a singular direction for an ambiguous OHLC candle."""
        session = _session(
            _range_candles()
            + (_candle(9, 30, high=107.0, low=97.0, close=102.0),)
        )
        opening_range = extract_opening_range(session, duration=timedelta(minutes=15))

        with self.assertRaisesRegex(ValueError, "singular escape event"):
            find_first_escape_event(opening_range, session)


def _range_candles() -> tuple[Candle, ...]:
    """Create three canonical candles with an observed high of 106 and low of 98."""
    return (
        _candle(9, 15, open_price=100.0, high=102.0, low=99.0, close=101.0),
        _candle(9, 20, open_price=101.0, high=106.0, low=100.0, close=105.0),
        _candle(9, 25, open_price=105.0, high=105.0, low=98.0, close=104.0),
    )


def _session(candles: tuple[Candle, ...]) -> Session:
    """Create a canonical M5 session for observed-event tests."""
    return Session(
        session_date=date(2026, 7, 17),
        instrument=Instrument.BANKNIFTY,
        timeframe=Timeframe.M5,
        weekday=Weekday.FRIDAY,
        is_weekly_expiry=None,
        is_monthly_expiry=None,
        has_holiday_gap=None,
        candles=candles,
    )


def _candle(
    hour: int,
    minute: int,
    *,
    open_price: float = 100.0,
    high: float = 102.0,
    low: float = 99.0,
    close: float = 101.0,
) -> Candle:
    """Create an immutable canonical candle at an Asia/Kolkata timestamp."""
    return Candle(
        instrument=Instrument.BANKNIFTY,
        timeframe=Timeframe.M5,
        timestamp=_timestamp(hour, minute),
        session_date=date(2026, 7, 17),
        open=open_price,
        high=high,
        low=low,
        close=close,
        volume=1,
    )


def _timestamp(hour: int, minute: int) -> datetime:
    """Return a canonical Asia/Kolkata test timestamp."""
    return datetime(2026, 7, 17, hour, minute, tzinfo=ZoneInfo("Asia/Kolkata"))
