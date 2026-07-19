"""Contract tests for M2.7 immutable session construction."""

from dataclasses import FrozenInstanceError
from datetime import date, datetime
import unittest

from src.engines.data import (
    Candle,
    Instrument,
    SessionConstructionError,
    SessionMetadata,
    Timeframe,
    Weekday,
    build_session,
    build_sessions,
)


class SessionConstructionContractTests(unittest.TestCase):
    """Verify construction uses canonical candles without quality inference."""

    def test_build_session_uses_unknown_metadata_by_default(self) -> None:
        """Omitted metadata must retain unknown facts as None."""
        candle = _candle(session_date=date(2026, 7, 17), minute=15)

        session = build_session((candle,))

        self.assertEqual(session.weekday, Weekday.FRIDAY)
        self.assertIsNone(session.is_weekly_expiry)
        self.assertIsNone(session.is_monthly_expiry)
        self.assertIsNone(session.has_holiday_gap)
        self.assertEqual(session.candles, (candle,))

    def test_build_session_preserves_explicit_tri_state_metadata(self) -> None:
        """Construction copies supplied facts without inferring the remainder."""
        metadata = SessionMetadata(is_weekly_expiry=True, has_holiday_gap=False)

        session = build_session(
            (_candle(session_date=date(2026, 7, 17), minute=15),),
            metadata=metadata,
        )

        self.assertTrue(session.is_weekly_expiry)
        self.assertIsNone(session.is_monthly_expiry)
        self.assertFalse(session.has_holiday_gap)
        with self.assertRaises(FrozenInstanceError):
            metadata.is_weekly_expiry = False

    def test_build_sessions_groups_and_orders_sessions_deterministically(self) -> None:
        """Output sorting must not alter the supplied order within a group."""
        later = _candle(session_date=date(2026, 7, 20), minute=15)
        first = _candle(session_date=date(2026, 7, 17), minute=15)
        second = _candle(session_date=date(2026, 7, 17), minute=20)

        sessions = build_sessions((later, first, second))

        self.assertEqual(
            [session.session_date for session in sessions],
            [date(2026, 7, 17), date(2026, 7, 20)],
        )
        self.assertEqual(sessions[0].candles, (first, second))
        self.assertIsNone(sessions[0].is_weekly_expiry)
        self.assertIsNone(sessions[1].has_holiday_gap)

    def test_build_sessions_uses_metadata_only_for_matching_groups(self) -> None:
        """Missing group metadata remains unknown rather than becoming false."""
        session_date = date(2026, 7, 17)
        candle = _candle(session_date=session_date, minute=15)
        key = (session_date, Instrument.BANKNIFTY, Timeframe.M5)

        (session,) = build_sessions((candle,), metadata_by_session={key: SessionMetadata(True)})

        self.assertTrue(session.is_weekly_expiry)
        self.assertIsNone(session.is_monthly_expiry)
        self.assertIsNone(session.has_holiday_gap)

    def test_extra_metadata_is_not_silently_ignored(self) -> None:
        """Metadata keys without sessions must fail deterministically."""
        candle = _candle(session_date=date(2026, 7, 17), minute=15)
        extra_key = (date(2026, 7, 20), Instrument.BANKNIFTY, Timeframe.M5)

        with self.assertRaisesRegex(
            SessionConstructionError,
            "Session metadata contains entries for unconstructed sessions.",
        ):
            build_sessions((candle,), metadata_by_session={extra_key: SessionMetadata()})

    def test_build_session_rejects_mixed_canonical_grouping_values(self) -> None:
        """One Session represents exactly one canonical session key."""
        first = _candle(session_date=date(2026, 7, 17), minute=15)
        other_date = _candle(session_date=date(2026, 7, 20), minute=20)

        with self.assertRaises(SessionConstructionError):
            build_session((first, other_date))

    def test_duplicate_and_descending_timestamps_are_rejected(self) -> None:
        """Session construction requires strict input order and never sorts it."""
        first = _candle(session_date=date(2026, 7, 17), minute=15)
        duplicate = _candle(session_date=date(2026, 7, 17), minute=15)
        earlier = _candle(session_date=date(2026, 7, 17), minute=10)

        with self.assertRaisesRegex(SessionConstructionError, "duplicate timestamps"):
            build_session((first, duplicate))
        with self.assertRaisesRegex(SessionConstructionError, "strictly timestamp-ordered"):
            build_session((first, earlier))

    def test_partial_and_semantically_invalid_sessions_are_constructed(self) -> None:
        """Completeness and candle validation remain outside this milestone."""
        candle = _candle(
            session_date=date(2026, 7, 17),
            minute=15,
            open_price=100.0,
            high=90.0,
        )

        session = build_session((candle,))

        self.assertEqual(session.candles, (candle,))

    def test_empty_input_and_invalid_metadata_are_rejected(self) -> None:
        """Programming-contract failures must be explicit."""
        with self.assertRaises(SessionConstructionError):
            build_session(())
        with self.assertRaises(TypeError):
            SessionMetadata(is_weekly_expiry="yes")
        with self.assertRaises(TypeError):
            build_session((_candle(session_date=date(2026, 7, 17), minute=15),), metadata=True)


def _candle(
    *,
    session_date: date,
    minute: int,
    open_price: float = 100.0,
    high: float = 101.0,
) -> Candle:
    """Create a canonical-looking candle for construction contract tests."""
    return Candle(
        instrument=Instrument.BANKNIFTY,
        timeframe=Timeframe.M5,
        timestamp=datetime(session_date.year, session_date.month, session_date.day, 9, minute),
        session_date=session_date,
        open=open_price,
        high=high,
        low=99.0,
        close=100.5,
        volume=1,
    )


if __name__ == "__main__":
    unittest.main()
