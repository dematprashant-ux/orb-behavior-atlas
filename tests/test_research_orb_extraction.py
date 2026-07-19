"""Contract tests for deterministic canonical opening-range extraction."""

from datetime import date, datetime, timedelta
from unittest import TestCase
from zoneinfo import ZoneInfo

from src.engines.data.models import Candle, Instrument, Session, Timeframe, Weekday
from src.engines.research import OpeningRange, extract_opening_range


class OpeningRangeExtractionTests(TestCase):
    """Verify extraction uses only ordered canonical candles from one session."""

    def test_extracts_the_expected_observed_values_and_candles(self) -> None:
        """Use the first three M5 candles for an inclusive 15-minute window."""
        session = _session_with_candles()

        opening_range = extract_opening_range(session, duration=timedelta(minutes=15))

        self.assertIsInstance(opening_range, OpeningRange)
        self.assertEqual(opening_range.window.start_timestamp, _timestamp(9, 15))
        self.assertEqual(opening_range.window.end_timestamp, _timestamp(9, 30))
        self.assertEqual(opening_range.open, 100.0)
        self.assertEqual(opening_range.high, 106.0)
        self.assertEqual(opening_range.low, 98.0)
        self.assertEqual(opening_range.close, 104.0)
        self.assertEqual(opening_range.candles, session.candles[:3])

    def test_excludes_the_candle_at_the_exclusive_window_end(self) -> None:
        """Keep the 09:30 candle outside the canonical 09:15-to-09:30 window."""
        session = _session_with_candles()

        opening_range = extract_opening_range(session, duration=timedelta(minutes=15))

        self.assertNotIn(session.candles[3], opening_range.candles)
        self.assertEqual(opening_range.candles[-1].timestamp, _timestamp(9, 25))

    def test_rejects_insufficient_or_irregular_candles(self) -> None:
        """Require all canonical timestamps needed by the requested window."""
        with self.assertRaisesRegex(ValueError, "exceeds available"):
            extract_opening_range(
                _session(_session_with_candles().candles[:2]),
                duration=timedelta(minutes=15),
            )

        irregular_session = _session(
            (_candle(9, 15), _candle(9, 25), _candle(9, 30))
        )
        with self.assertRaisesRegex(ValueError, "required canonical"):
            extract_opening_range(irregular_session, duration=timedelta(minutes=15))

    def test_rejects_non_positive_or_unaligned_durations(self) -> None:
        """Require a positive whole number of canonical timeframe intervals."""
        session = _session_with_candles()

        for duration in (timedelta(), timedelta(minutes=-5), timedelta(minutes=1)):
            with self.assertRaises(ValueError):
                extract_opening_range(session, duration=duration)

    def test_repeated_execution_is_deterministic_and_does_not_mutate_input(self) -> None:
        """Return equal facts while retaining the original immutable session candles."""
        session = _session_with_candles()
        original_candles = session.candles

        first = extract_opening_range(session, duration=timedelta(minutes=15))
        second = extract_opening_range(session, duration=timedelta(minutes=15))

        self.assertEqual(first, second)
        self.assertIs(session.candles, original_candles)
        self.assertEqual(session.candles, original_candles)


def _session_with_candles() -> Session:
    """Create one canonical session with four sequential M5 candles."""
    return _session(
        (
            _candle(9, 15, open_price=100.0, high=102.0, low=99.0, close=101.0),
            _candle(9, 20, open_price=101.0, high=106.0, low=100.0, close=105.0),
            _candle(9, 25, open_price=105.0, high=105.0, low=98.0, close=104.0),
            _candle(9, 30, open_price=104.0, high=107.0, low=103.0, close=106.0),
        )
    )


def _session(candles: tuple[Candle, ...]) -> Session:
    """Create a canonical session reference for extraction tests."""
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
    """Create one canonical M5 candle at the supplied Asia/Kolkata timestamp."""
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
