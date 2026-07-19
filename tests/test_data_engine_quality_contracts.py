"""Contract tests for M2.9 read-only data-quality assessment."""

from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import date, datetime, timedelta
from inspect import Parameter, signature
from typing import get_type_hints
import unittest

from src.engines.data import (
    Candle,
    DataQualityReport,
    Instrument,
    QualityCode,
    QualityIssue,
    QualitySeverity,
    Session,
    SessionQualityMetrics,
    SessionQualityResult,
    Timeframe,
    Weekday,
    assess_session,
    assess_sessions,
)


class DataQualityContractTests(unittest.TestCase):
    """Verify quality assessment observes immutable constructed sessions only."""

    def test_quality_api_accepts_sessions_and_preserves_their_order(self) -> None:
        """Expose only the approved single- and multi-session entry points."""
        self._assert_session_parameter(assess_session)
        self._assert_sessions_parameter(assess_sessions)

        later = _session(session_date=date(2026, 7, 24), minutes=(15, 20))
        earlier = _session(session_date=date(2026, 7, 17), minutes=(15, 20))

        report = assess_sessions((later, earlier))

        self.assertEqual(
            [result.session.session_date for result in report.sessions],
            [date(2026, 7, 24), date(2026, 7, 17)],
        )

    def test_expected_interval_is_derived_from_the_timeframe_model(self) -> None:
        """Keep quality rules independent from a hardcoded M5 duration."""
        session = _session(minutes=(15, 25))

        result = assess_session(session)

        self.assertEqual(Timeframe.M5.duration, timedelta(minutes=5))
        self.assertEqual(len(result.issues), 1)
        self.assertEqual(result.issues[0].expected_interval, Timeframe.M5.duration)
        self.assertEqual(result.issues[0].observed_interval, timedelta(minutes=10))

    def test_unconfigured_timeframe_duration_fails_deterministically(self) -> None:
        """Require future timeframes to declare a canonical quality duration."""

        class UnconfiguredTimeframe:
            """Represents a future enum member missing its duration configuration."""

            value = "UNCONFIGURED"

        with self.assertRaisesRegex(
            ValueError,
            "No canonical duration is configured for timeframe UNCONFIGURED.",
        ):
            Timeframe.duration.fget(UnconfiguredTimeframe())

    def test_unexpected_interval_issue_is_self_contained_and_observational(self) -> None:
        """Describe irregular spacing with canonical values rather than candle objects."""
        session = _session(minutes=(15, 25))

        (issue,) = assess_session(session).issues

        self.assertEqual(issue.code, QualityCode.UNEXPECTED_INTERVAL)
        self.assertEqual(issue.severity, QualitySeverity.WARNING)
        self.assertEqual(issue.previous_timestamp, datetime(2026, 7, 17, 9, 15))
        self.assertEqual(issue.current_timestamp, datetime(2026, 7, 17, 9, 25))
        self.assertEqual(issue.expected_interval, timedelta(minutes=5))
        self.assertEqual(issue.observed_interval, timedelta(minutes=10))
        self.assertFalse(
            any(isinstance(getattr(issue, field.name), Candle) for field in fields(issue))
        )

    def test_expected_spacing_produces_metrics_without_findings(self) -> None:
        """Observe complete local spacing without inferring market-day completeness."""
        session = _session(minutes=(15, 20, 25))

        result = assess_session(session)

        self.assertEqual(result.issues, ())
        self.assertEqual(result.metrics.candle_count, 3)
        self.assertEqual(result.metrics.unexpected_interval_count, 0)
        self.assertEqual(result.metrics.first_timestamp, datetime(2026, 7, 17, 9, 15))
        self.assertEqual(result.metrics.last_timestamp, datetime(2026, 7, 17, 9, 25))

    def test_empty_batch_is_valid_and_report_totals_are_derived(self) -> None:
        """Return immutable empty observations without assuming missing sessions."""
        report = assess_sessions(())

        self.assertEqual(report.sessions, ())
        self.assertEqual(report.session_count, 0)
        self.assertEqual(report.candle_count, 0)
        self.assertEqual(report.unexpected_interval_count, 0)

    def test_quality_models_are_immutable_and_use_stable_values(self) -> None:
        """Keep reports safe for downstream research consumers."""
        session = _session(minutes=(15, 25))
        result = assess_session(session)
        issue = result.issues[0]

        self.assertEqual(list(QualitySeverity), [
            QualitySeverity.INFO,
            QualitySeverity.WARNING,
            QualitySeverity.ERROR,
        ])
        self.assertEqual(QualityCode.UNEXPECTED_INTERVAL.value, "UNEXPECTED_INTERVAL")
        self.assertTrue(
            all(
                is_dataclass(model)
                for model in (issue, result.metrics, result, DataQualityReport((result,)))
            )
        )
        with self.assertRaises(FrozenInstanceError):
            issue.message = "changed"

    def test_quality_assessment_rejects_invalid_public_inputs(self) -> None:
        """Reserve exceptions for programming-contract errors, not findings."""
        with self.assertRaises(TypeError):
            assess_session("not a session")
        with self.assertRaises(TypeError):
            assess_sessions((_session(minutes=(15, 20)), "not a session"))

    def _assert_session_parameter(self, function: object) -> None:
        """Verify the single-session API is narrow and typed."""
        function_signature = signature(function)
        self.assertEqual(list(function_signature.parameters), ["session"])
        parameter = function_signature.parameters["session"]
        self.assertIs(parameter.kind, Parameter.POSITIONAL_OR_KEYWORD)
        self.assertEqual(
            get_type_hints(function),
            {"session": Session, "return": SessionQualityResult},
        )

    def _assert_sessions_parameter(self, function: object) -> None:
        """Verify the batch API accepts only constructed session sequences."""
        function_signature = signature(function)
        self.assertEqual(list(function_signature.parameters), ["sessions"])
        parameter = function_signature.parameters["sessions"]
        self.assertIs(parameter.kind, Parameter.POSITIONAL_OR_KEYWORD)
        self.assertEqual(
            get_type_hints(function)["return"],
            DataQualityReport,
        )


def _session(*, session_date: date = date(2026, 7, 17), minutes: tuple[int, ...]) -> Session:
    """Create a canonical-looking immutable session for quality contracts."""
    candles = tuple(
        Candle(
            instrument=Instrument.BANKNIFTY,
            timeframe=Timeframe.M5,
            timestamp=datetime(
                session_date.year,
                session_date.month,
                session_date.day,
                9,
                minute,
            ),
            session_date=session_date,
            open=100.0,
            high=101.0,
            low=99.0,
            close=100.5,
            volume=1,
        )
        for minute in minutes
    )
    return Session(
        session_date=session_date,
        instrument=Instrument.BANKNIFTY,
        timeframe=Timeframe.M5,
        weekday=Weekday.FRIDAY,
        is_weekly_expiry=None,
        is_monthly_expiry=None,
        has_holiday_gap=None,
        candles=candles,
    )


if __name__ == "__main__":
    unittest.main()
