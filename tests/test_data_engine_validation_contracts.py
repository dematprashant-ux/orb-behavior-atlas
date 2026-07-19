"""Contract tests for canonical candle validation."""

from dataclasses import FrozenInstanceError, is_dataclass
from datetime import date, datetime, timezone
from inspect import Parameter, signature
import unittest
from zoneinfo import ZoneInfo

from src.engines.data import (
    Candle,
    CandleValidationResult,
    Instrument,
    Timeframe,
    ValidationCode,
    ValidationIssue,
    ValidationSeverity,
    validate_candle,
    validate_candles,
)


class DataEngineValidationContractTests(unittest.TestCase):
    """Verify structured, canonical candle validation behavior."""

    def test_public_api_is_typed_and_preserves_m2_3_protocols(self) -> None:
        """Expose validation without modifying Data Engine provider contracts."""
        self.assertEqual(list(signature(validate_candle).parameters), ["candle"])
        batch_signature = signature(validate_candles)
        self.assertEqual(
            list(batch_signature.parameters),
            ["candles", "check_duplicates", "check_timestamp_order"],
        )
        self.assertIs(
            batch_signature.parameters["check_duplicates"].kind,
            Parameter.KEYWORD_ONLY,
        )
        self.assertIs(
            batch_signature.parameters["check_timestamp_order"].kind,
            Parameter.KEYWORD_ONLY,
        )

    def test_valid_candle_returns_an_empty_immutable_issue_collection(self) -> None:
        """Treat zero prices and zero volume as valid canonical values."""
        result = validate_candle(self._candle(open=0.0, high=0.0, low=0.0, close=0.0, volume=0))
        self.assertTrue(result.is_valid)
        self.assertEqual(result.issues, ())
        self.assertTrue(is_dataclass(result))
        self.assertTrue(is_dataclass(ValidationIssue))
        with self.assertRaises(FrozenInstanceError):
            result.issues = ()

    def test_each_ohlc_rule_reports_its_stable_code_and_rule_identifier(self) -> None:
        """Report every documented OHLC relationship as a separate issue."""
        cases = (
            (self._candle(high=99.0), ValidationCode.HIGH_BELOW_OPEN, "OHLC_HIGH_GE_OPEN"),
            (self._candle(high=100.25), ValidationCode.HIGH_BELOW_CLOSE, "OHLC_HIGH_GE_CLOSE"),
            (self._candle(high=98.0), ValidationCode.HIGH_BELOW_LOW, "OHLC_HIGH_GE_LOW"),
            (self._candle(low=101.0), ValidationCode.LOW_ABOVE_OPEN, "OHLC_LOW_LE_OPEN"),
            (self._candle(low=100.75), ValidationCode.LOW_ABOVE_CLOSE, "OHLC_LOW_LE_CLOSE"),
        )
        for candle, code, rule_id in cases:
            with self.subTest(code=code):
                issue = next(
                    issue for issue in validate_candle(candle).issues if issue.code is code
                )
                self.assertEqual(issue.severity, ValidationSeverity.ERROR)
                self.assertEqual(issue.rule_id, rule_id)

    def test_negative_price_and_volume_are_invalid_while_zero_is_valid(self) -> None:
        """Keep documented non-negative value rules independent from normalization."""
        result = validate_candle(self._candle(open=-1.0, volume=-1))
        self.assertIn(
            (ValidationCode.NEGATIVE_PRICE, "open"),
            [(issue.code, issue.field) for issue in result.issues],
        )
        self.assertIn(
            (ValidationCode.NEGATIVE_VOLUME, "volume"),
            [(issue.code, issue.field) for issue in result.issues],
        )

    def test_timestamp_and_session_date_rules_are_accumulative(self) -> None:
        """Report canonical timestamp requirements without mutating the candle."""
        naive = self._candle(timestamp=datetime(2026, 7, 17, 9, 15), session_date=date(2026, 7, 18))
        utc = self._candle(timestamp=datetime(2026, 7, 17, 3, 45, tzinfo=timezone.utc))
        self.assertEqual(
            [issue.code for issue in validate_candle(naive).issues],
            [ValidationCode.TIMESTAMP_NAIVE, ValidationCode.SESSION_DATE_MISMATCH],
        )
        self.assertEqual(
            [issue.code for issue in validate_candle(utc).issues],
            [ValidationCode.TIMESTAMP_NOT_ASIA_KOLKATA],
        )

    def test_multiple_issues_follow_the_documented_stable_order(self) -> None:
        """Preserve deterministic issue ordering for downstream quality aggregation."""
        result = validate_candle(self._candle(high=90.0, low=110.0, close=100.0, volume=-1))
        self.assertEqual(
            [issue.code for issue in result.issues],
            [
                ValidationCode.HIGH_BELOW_OPEN,
                ValidationCode.HIGH_BELOW_CLOSE,
                ValidationCode.HIGH_BELOW_LOW,
                ValidationCode.LOW_ABOVE_OPEN,
                ValidationCode.LOW_ABOVE_CLOSE,
                ValidationCode.NEGATIVE_VOLUME,
            ],
        )
        self.assertTrue(all(issue.severity is ValidationSeverity.ERROR for issue in result.issues))

    def test_unsupported_instrument_and_timeframe_are_reported(self) -> None:
        """Return semantic findings instead of request-boundary exceptions."""
        candle = self._candle()
        object.__setattr__(candle, "instrument", "NIFTY")
        object.__setattr__(candle, "timeframe", "M1")
        self.assertEqual(
            [issue.code for issue in validate_candle(candle).issues],
            [ValidationCode.UNSUPPORTED_INSTRUMENT, ValidationCode.UNSUPPORTED_TIMEFRAME],
        )

    def test_batch_duplicate_and_order_rules_use_canonical_timestamps(self) -> None:
        """Attach batch findings to later input records without sorting input."""
        candles = (
            self._candle(timestamp=self._timestamp(9, 15)),
            self._candle(timestamp=self._timestamp(9, 20)),
            self._candle(timestamp=self._timestamp(9, 20)),
            self._candle(timestamp=self._timestamp(9, 18)),
        )
        results = validate_candles(candles)

        self.assertEqual([result.candle for result in results], list(candles))
        self.assertEqual(
            [(issue.code, issue.related_index, issue.rule_id) for issue in results[2].issues],
            [(ValidationCode.DUPLICATE_TIMESTAMP, 1, "TIMESTAMP_UNIQUE")],
        )
        self.assertEqual(
            [(issue.code, issue.related_index, issue.rule_id) for issue in results[3].issues],
            [(ValidationCode.TIMESTAMP_OUT_OF_ORDER, 2, "TIMESTAMP_NONDECREASING")],
        )

    def test_batch_checks_can_be_disabled_and_empty_input_is_valid(self) -> None:
        """Provide optional batch checks without introducing quality aggregation."""
        duplicate = self._candle(timestamp=self._timestamp(9, 15))
        results = validate_candles(
            (self._candle(timestamp=self._timestamp(9, 15)), duplicate),
            check_duplicates=False,
            check_timestamp_order=False,
        )
        self.assertTrue(all(result.is_valid for result in results))
        self.assertEqual(validate_candles(()), ())

    def test_contract_errors_are_reserved_for_invalid_api_inputs(self) -> None:
        """Keep normal semantic validation failures out of the exception path."""
        with self.assertRaises(TypeError):
            validate_candle(object())
        with self.assertRaises(TypeError):
            validate_candles((self._candle(), object()))
        with self.assertRaises(TypeError):
            validate_candles((), check_duplicates=1)

    @staticmethod
    def _timestamp(hour: int, minute: int) -> datetime:
        """Return a canonical Asia/Kolkata timestamp for a test candle."""
        return datetime(2026, 7, 17, hour, minute, tzinfo=ZoneInfo("Asia/Kolkata"))

    def _candle(
        self,
        *,
        timestamp: datetime | None = None,
        session_date: date | None = None,
        open: float = 100.0,
        high: float = 101.0,
        low: float = 99.0,
        close: float = 100.5,
        volume: int = 1,
    ) -> Candle:
        """Return a valid canonical candle with targeted override support."""
        candle_timestamp = timestamp or self._timestamp(9, 15)
        return Candle(
            instrument=Instrument.BANKNIFTY,
            timeframe=Timeframe.M5,
            timestamp=candle_timestamp,
            session_date=session_date or candle_timestamp.date(),
            open=open,
            high=high,
            low=low,
            close=close,
            volume=volume,
        )


if __name__ == "__main__":
    unittest.main()
