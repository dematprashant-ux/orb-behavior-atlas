"""Contract tests for objective post-escape ORB observations."""

from dataclasses import FrozenInstanceError, is_dataclass
from datetime import date, datetime, timedelta
from unittest import TestCase
from zoneinfo import ZoneInfo

from src.engines.data.models import Candle, Instrument, Session, Timeframe, Weekday
from src.engines.research import (
    ORBPostEscapeObservation,
    extract_opening_range,
    find_first_escape_event,
    observe_post_escape,
)


class ORBPostEscapeObservationTests(TestCase):
    """Verify objective post-escape facts without behavior classification."""

    def test_observes_upward_continuation_facts(self) -> None:
        """Measure post-event extremes and boundary-relative excursions only."""
        session = _session(
            _range_candles()
            + (
                _candle(9, 30, high=107.0, low=103.0, close=106.0),
                _candle(9, 35, high=110.0, low=107.0, close=109.0),
                _candle(9, 40, high=112.0, low=108.0, close=111.0),
            )
        )

        observation = _observe(session)

        self.assertIsInstance(observation, ORBPostEscapeObservation)
        self.assertEqual(observation.highest_price, 112.0)
        self.assertEqual(observation.lowest_price, 107.0)
        self.assertEqual(observation.maximum_favorable_excursion, 6.0)
        self.assertEqual(observation.maximum_adverse_excursion, 0.0)
        self.assertFalse(observation.returned_inside_range)
        self.assertIsNone(observation.first_return_inside_timestamp)

    def test_records_the_first_post_escape_return_inside_the_range(self) -> None:
        """Record only the first timestamp whose price interval re-enters range."""
        session = _session(
            _range_candles()
            + (
                _candle(9, 30, high=107.0, low=103.0, close=106.0),
                _candle(9, 35, high=109.0, low=107.0, close=108.0),
                _candle(9, 40, high=108.0, low=105.0, close=106.0),
                _candle(9, 45, high=107.0, low=104.0, close=105.0),
            )
        )

        observation = _observe(session)

        self.assertTrue(observation.returned_inside_range)
        self.assertEqual(observation.first_return_inside_timestamp, _timestamp(9, 40))

    def test_measures_downward_boundary_relative_excursions(self) -> None:
        """Invert favorable and adverse distance consistently for downward escape."""
        session = _session(
            _range_candles()
            + (
                _candle(9, 30, high=95.0, low=97.0, close=97.0),
                _candle(9, 35, high=97.0, low=94.0, close=95.0),
            )
        )

        observation = _observe(session)

        self.assertEqual(observation.highest_price, 97.0)
        self.assertEqual(observation.lowest_price, 94.0)
        self.assertEqual(observation.maximum_favorable_excursion, 4.0)
        self.assertEqual(observation.maximum_adverse_excursion, 0.0)

    def test_returns_no_return_when_subsequent_candles_remain_outside_range(self) -> None:
        """Keep no-return distinct from any later breakout interpretation."""
        session = _session(
            _range_candles()
            + (
                _candle(9, 30, high=107.0, low=103.0, close=106.0),
                _candle(9, 35, high=109.0, low=107.0, close=108.0),
            )
        )

        observation = _observe(session)

        self.assertFalse(observation.returned_inside_range)
        self.assertIsNone(observation.first_return_inside_timestamp)

    def test_empty_post_escape_history_uses_unknown_extrema_and_excursions(self) -> None:
        """Do not fabricate measurements when no candles follow the escape event."""
        session = _session(
            _range_candles()
            + (_candle(9, 30, high=107.0, low=103.0, close=106.0),)
        )

        observation = _observe(session)

        self.assertIsNone(observation.highest_price)
        self.assertIsNone(observation.lowest_price)
        self.assertIsNone(observation.maximum_favorable_excursion)
        self.assertIsNone(observation.maximum_adverse_excursion)
        self.assertFalse(observation.returned_inside_range)
        self.assertIsNone(observation.first_return_inside_timestamp)

    def test_repeated_execution_is_deterministic_and_output_is_immutable(self) -> None:
        """Preserve canonical inputs while returning an immutable factual record."""
        session = _session(
            _range_candles()
            + (
                _candle(9, 30, high=107.0, low=103.0, close=106.0),
                _candle(9, 35, high=110.0, low=107.0, close=109.0),
            )
        )

        first = _observe(session)
        second = _observe(session)

        self.assertEqual(first, second)
        self.assertTrue(is_dataclass(first))
        self.assertFalse(hasattr(first, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            first.highest_price = 0.0

    def test_rejects_an_escape_event_not_belonging_to_the_session(self) -> None:
        """Require the supplied event to be the session's first canonical escape."""
        source_session = _session(
            _range_candles()
            + (_candle(9, 30, high=107.0, low=103.0, close=106.0),)
        )
        opening_range = extract_opening_range(source_session, duration=timedelta(minutes=15))
        escape_event = find_first_escape_event(opening_range, source_session)
        other_session = _session(
            _range_candles()
            + (_candle(9, 30, high=105.0, low=99.0, close=102.0),)
        )

        with self.assertRaisesRegex(ValueError, "does not belong"):
            observe_post_escape(opening_range, escape_event, other_session)


def _observe(session: Session) -> ORBPostEscapeObservation:
    """Extract the canonical range and first event before observing later candles."""
    opening_range = extract_opening_range(session, duration=timedelta(minutes=15))
    escape_event = find_first_escape_event(opening_range, session)
    return observe_post_escape(opening_range, escape_event, session)


def _range_candles() -> tuple[Candle, ...]:
    """Create a canonical range with high 106 and low 98 for observation tests."""
    return (
        _candle(9, 15, open_price=100.0, high=102.0, low=99.0, close=101.0),
        _candle(9, 20, open_price=101.0, high=106.0, low=100.0, close=105.0),
        _candle(9, 25, open_price=105.0, high=105.0, low=98.0, close=104.0),
    )


def _session(candles: tuple[Candle, ...]) -> Session:
    """Create a canonical M5 session for observation tests."""
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
    """Create a canonical M5 candle at the supplied Asia/Kolkata timestamp."""
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
