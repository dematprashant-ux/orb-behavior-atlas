"""Behavioral tests for deterministic per-session BANKNIFTY M5 quality outcomes."""

from dataclasses import FrozenInstanceError, is_dataclass
from datetime import date, datetime, timedelta
from unittest import TestCase
from zoneinfo import ZoneInfo

from src.engines.data import (
    Candle,
    DataEngineExecutionRequest,
    DataEngineOrchestrator,
    ExecutionStatus,
    Instrument,
    MarketSessionQualityResult,
    MarketSessionQualityStatus,
    MarketSessionRejectionCode,
    Session,
    Timeframe,
    Weekday,
    evaluate_market_session_qualities,
    evaluate_market_session_quality,
)

_SESSION_DATE = date(2026, 7, 17)
_TIMEZONE = ZoneInfo("Asia/Kolkata")


class MarketSessionQualityTests(TestCase):
    """Verify complete, partial, and rejected outcomes retain source sessions."""

    def test_complete_regular_session_is_accepted_unchanged_and_immutable(self) -> None:
        """The exact full M5 bar-open sequence is a complete valid session."""
        session = _session(_regular_candles())

        result = evaluate_market_session_quality(session)

        self.assertIs(result.session, session)
        self.assertIs(result.status, MarketSessionQualityStatus.VALID_COMPLETE_SESSION)
        self.assertEqual(result.rejections, ())
        self.assertTrue(is_dataclass(result))
        with self.assertRaises(FrozenInstanceError):
            result.status = MarketSessionQualityStatus.REJECTED_SESSION

    def test_leading_and_trailing_missing_bars_are_valid_partial_sessions(self) -> None:
        """Only missing bars inside the observed span are rejected by the policy."""
        candles = _regular_candles()
        leading = _session(candles[1:])
        trailing = _session(candles[:-1])

        for session in (leading, trailing):
            with self.subTest(session=session):
                result = evaluate_market_session_quality(session)
                self.assertIs(
                    result.status,
                    MarketSessionQualityStatus.VALID_PARTIAL_SESSION,
                )
                self.assertEqual(result.rejections, ())

    def test_semantic_validation_failures_are_rejected_with_stable_details(
        self,
    ) -> None:
        """Existing OHLC and volume validation facts are reused without duplication."""
        invalid_ohlc = _session((_candle(9, 15, high=99.0),))
        invalid_volume = _session((_candle(9, 15, volume=-1),))

        self.assertIn(
            (MarketSessionRejectionCode.CANDLE_VALIDATION, "HIGH_BELOW_OPEN"),
            _rejection_details(evaluate_market_session_quality(invalid_ohlc)),
        )
        self.assertEqual(
            _rejection_details(evaluate_market_session_quality(invalid_volume)),
            [(MarketSessionRejectionCode.CANDLE_VALIDATION, "NEGATIVE_VOLUME")],
        )

    def test_duplicate_and_descending_timestamps_are_rejected(self) -> None:
        """Existing batch validation controls duplicate and ordering semantics."""
        duplicate = _session((_candle(9, 15), _candle(9, 15)))
        descending = _session((_candle(9, 20), _candle(9, 15)))

        self.assertEqual(
            _rejection_details(evaluate_market_session_quality(duplicate)),
            [(MarketSessionRejectionCode.CANDLE_VALIDATION, "DUPLICATE_TIMESTAMP")],
        )
        self.assertEqual(
            _rejection_details(evaluate_market_session_quality(descending)),
            [
                (
                    MarketSessionRejectionCode.CANDLE_VALIDATION,
                    "TIMESTAMP_OUT_OF_ORDER",
                )
            ],
        )

    def test_internal_missing_m5_bar_is_rejected(self) -> None:
        """Spacing assessment turns an observed internal gap into a rejection."""
        result = evaluate_market_session_quality(
            _session((_candle(9, 15), _candle(9, 25)))
        )

        self.assertEqual(
            _rejection_details(result),
            [(MarketSessionRejectionCode.INTERNAL_M5_GAP, "UNEXPECTED_INTERVAL")],
        )

    def test_timestamps_outside_the_regular_bar_open_interval_are_rejected(
        self,
    ) -> None:
        """The documented 09:15 inclusive and 15:30 exclusive bounds are enforced."""
        before = _session((_candle(9, 10),))
        end_boundary = _session((_candle(15, 30),))

        for session in (before, end_boundary):
            with self.subTest(session=session):
                self.assertEqual(
                    _rejection_details(evaluate_market_session_quality(session)),
                    [(MarketSessionRejectionCode.OUTSIDE_REGULAR_SESSION, None)],
                )

    def test_unaligned_and_empty_sessions_are_rejected(self) -> None:
        """A timestamp must be an M5 bar open and a session must contain a bar."""
        unaligned = _session((_candle(9, 16),))
        empty = _session(())

        self.assertEqual(
            _rejection_details(evaluate_market_session_quality(unaligned)),
            [(MarketSessionRejectionCode.UNALIGNED_M5_TIMESTAMP, None)],
        )
        self.assertEqual(
            _rejection_details(evaluate_market_session_quality(empty)),
            [(MarketSessionRejectionCode.EMPTY_SESSION, None)],
        )

    def test_batch_outcomes_preserve_order_and_repeated_results_are_equal(self) -> None:
        """Every supplied session has one deterministic result in source order."""
        sessions = (
            _session(_regular_candles()),
            _session((_candle(9, 15), _candle(9, 25))),
            _session(_regular_candles()[1:]),
        )

        first = evaluate_market_session_qualities(sessions)
        second = evaluate_market_session_qualities(sessions)

        self.assertEqual(first, second)
        self.assertEqual([result.session for result in first], list(sessions))
        self.assertEqual(
            [result.status for result in first],
            [
                MarketSessionQualityStatus.VALID_COMPLETE_SESSION,
                MarketSessionQualityStatus.REJECTED_SESSION,
                MarketSessionQualityStatus.VALID_PARTIAL_SESSION,
            ],
        )

    def test_existing_data_engine_orchestrator_behavior_is_unchanged(self) -> None:
        """The separate evaluator does not alter batch orchestration results."""
        result = DataEngineOrchestrator().execute(
            _InvalidSource(),
            DataEngineExecutionRequest(
                instrument=Instrument.BANKNIFTY,
                timeframe=Timeframe.M5,
                start_date=_SESSION_DATE,
                end_date=_SESSION_DATE,
            ),
        )

        self.assertIs(result.status, ExecutionStatus.REJECTED)
        self.assertEqual(result.sessions, ())


def _session(candles: tuple[Candle, ...]) -> Session:
    """Build a fixture session directly to exercise quality rejection outcomes."""
    return Session(
        session_date=_SESSION_DATE,
        instrument=Instrument.BANKNIFTY,
        timeframe=Timeframe.M5,
        weekday=Weekday.FRIDAY,
        is_weekly_expiry=None,
        is_monthly_expiry=None,
        has_holiday_gap=None,
        candles=candles,
    )


def _regular_candles() -> tuple[Candle, ...]:
    """Return the complete 09:15 through 15:25 regular M5 bar-open sequence."""
    start = _timestamp(9, 15)
    return tuple(
        Candle(
            instrument=Instrument.BANKNIFTY,
            timeframe=Timeframe.M5,
            timestamp=start + (timedelta(minutes=5) * index),
            session_date=_SESSION_DATE,
            open=100.0,
            high=101.0,
            low=99.0,
            close=100.5,
            volume=1,
        )
        for index in range(75)
    )


def _candle(
    hour: int,
    minute: int,
    *,
    high: float = 101.0,
    volume: int = 1,
) -> Candle:
    """Return one canonical candle with optional semantic invalidity."""
    return Candle(
        instrument=Instrument.BANKNIFTY,
        timeframe=Timeframe.M5,
        timestamp=_timestamp(hour, minute),
        session_date=_SESSION_DATE,
        open=100.0,
        high=high,
        low=99.0,
        close=100.5,
        volume=volume,
    )


def _timestamp(hour: int, minute: int) -> datetime:
    """Return one Asia/Kolkata canonical bar-open timestamp."""
    return datetime(
        _SESSION_DATE.year,
        _SESSION_DATE.month,
        _SESSION_DATE.day,
        hour,
        minute,
        tzinfo=_TIMEZONE,
    )


def _rejection_details(
    result: MarketSessionQualityResult,
) -> list[tuple[MarketSessionRejectionCode, str | None]]:
    """Project stable rejection audit fields for compact behavioral assertions."""
    return [(rejection.code, rejection.detail) for rejection in result.rejections]


class _InvalidSource:
    """Provide one semantically invalid candle through the unchanged source boundary."""

    def fetch(
        self,
        *,
        instrument: Instrument,
        timeframe: Timeframe,
        start_date: date,
        end_date: date,
    ) -> tuple[Candle, ...]:
        """Return an invalid candle without changing orchestration semantics."""
        return (_candle(9, 15, high=99.0),)
