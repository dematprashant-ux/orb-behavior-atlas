"""Contract tests for reusable canonical candle normalization."""

from datetime import datetime
from decimal import Decimal
from inspect import Parameter, signature
from math import inf, nan
from typing import get_type_hints
import unittest
from zoneinfo import ZoneInfo

from src.engines.data import Candle, DataEngineError, DataNormalizationError, Instrument, Timeframe
from src.engines.data.normalization import normalize_candle, normalize_candles


class DataEngineNormalizationContractTests(unittest.TestCase):
    """Verify canonicalization without provider, validation, or storage behavior."""

    def test_normalization_api_is_narrow_and_typed(self) -> None:
        """Expose canonical values rather than provider-specific field mappings."""
        method_signature = signature(normalize_candle)
        self.assertEqual(
            list(method_signature.parameters),
            ["values", "instrument", "timeframe", "source_timezone"],
        )
        for name in ("instrument", "timeframe", "source_timezone"):
            self.assertIs(method_signature.parameters[name].kind, Parameter.KEYWORD_ONLY)
        self.assertEqual(get_type_hints(normalize_candle)["return"], Candle)

    def test_normalize_candle_assigns_canonical_metadata_and_session_date(self) -> None:
        """Normalize values into the immutable Data Engine candle model."""
        candle = normalize_candle(
            self._values(timestamp=datetime(2026, 7, 17, 3, 45, tzinfo=ZoneInfo("UTC"))),
            instrument=Instrument.BANKNIFTY,
            timeframe=Timeframe.M5,
            source_timezone=ZoneInfo("UTC"),
        )

        self.assertEqual(candle.instrument, Instrument.BANKNIFTY)
        self.assertEqual(candle.timeframe, Timeframe.M5)
        self.assertEqual(candle.timestamp.tzinfo, ZoneInfo("Asia/Kolkata"))
        self.assertEqual(candle.timestamp.hour, 9)
        self.assertEqual(candle.timestamp.minute, 15)
        self.assertEqual(candle.session_date, candle.timestamp.date())
        self.assertEqual(candle.open, 100.25)
        self.assertEqual(candle.volume, 10)

    def test_naive_timestamp_uses_explicit_source_timezone(self) -> None:
        """Never infer a naive timestamp timezone from the host environment."""
        candle = normalize_candle(
            self._values(timestamp=datetime(2026, 7, 17, 9, 15)),
            instrument=Instrument.BANKNIFTY,
            timeframe=Timeframe.M5,
            source_timezone=ZoneInfo("Asia/Kolkata"),
        )
        self.assertEqual(candle.timestamp.hour, 9)
        self.assertEqual(candle.timestamp.minute, 15)

    def test_ambiguous_and_nonexistent_naive_timestamps_fail_safely(self) -> None:
        """Require adapters to disambiguate daylight-saving local timestamps."""
        timezone = ZoneInfo("America/New_York")
        for timestamp, reason in (
            (datetime(2026, 11, 1, 1, 30), "ambiguous"),
            (datetime(2026, 3, 8, 2, 30), "nonexistent"),
        ):
            with self.subTest(timestamp=timestamp):
                with self.assertRaisesRegex(DataNormalizationError, reason):
                    normalize_candle(
                        self._values(timestamp=timestamp),
                        instrument=Instrument.BANKNIFTY,
                        timeframe=Timeframe.M5,
                        source_timezone=timezone,
                    )

    def test_numeric_conversion_rejects_non_canonical_values(self) -> None:
        """Reject booleans, nulls, non-finite values, and fractional volume."""
        invalid_values = (
            {"open": True},
            {"high": None},
            {"low": nan},
            {"close": inf},
            {"volume": 1.0},
            {"volume": Decimal("1.5")},
            {"volume": "1.0"},
        )
        for update in invalid_values:
            with self.subTest(update=update):
                values = self._values()
                values.update(update)
                with self.assertRaises(DataNormalizationError) as raised:
                    normalize_candle(
                        values,
                        instrument=Instrument.BANKNIFTY,
                        timeframe=Timeframe.M5,
                        source_timezone=ZoneInfo("Asia/Kolkata"),
                    )
                self.assertNotIn("secret", str(raised.exception).lower())

    def test_missing_fields_use_deterministic_non_sensitive_messages(self) -> None:
        """Report canonical field context without serializing input values."""
        values = self._values()
        del values["close"]

        with self.assertRaises(DataNormalizationError) as raised:
            normalize_candle(
                values,
                instrument=Instrument.BANKNIFTY,
                timeframe=Timeframe.M5,
                source_timezone=ZoneInfo("Asia/Kolkata"),
            )

        self.assertEqual(
            str(raised.exception),
            "Cannot normalize candle: missing required field 'close'.",
        )

    def test_numeric_conversion_chains_internal_cause_without_leaking_value(self) -> None:
        """Retain conversion context without exposing provider data publicly."""
        values = self._values()
        values["open"] = "provider-secret-value"

        with self.assertRaises(DataNormalizationError) as raised:
            normalize_candle(
                values,
                instrument=Instrument.BANKNIFTY,
                timeframe=Timeframe.M5,
                source_timezone=ZoneInfo("Asia/Kolkata"),
            )

        self.assertEqual(
            str(raised.exception),
            "Cannot normalize candle: field 'open' must be a finite numeric value.",
        )
        self.assertNotIn("provider-secret-value", str(raised.exception))
        self.assertIsNotNone(raised.exception.__cause__)

    def test_batch_preserves_order_is_fail_fast_and_allows_empty_input(self) -> None:
        """Leave ordering and issue aggregation outside the normalizer."""
        timezone = ZoneInfo("Asia/Kolkata")
        normalized = normalize_candles(
            (
                self._values(timestamp=datetime(2026, 7, 17, 9, 20)),
                self._values(timestamp=datetime(2026, 7, 17, 9, 15)),
            ),
            instrument=Instrument.BANKNIFTY,
            timeframe=Timeframe.M5,
            source_timezone=timezone,
        )
        self.assertEqual([candle.timestamp.minute for candle in normalized], [20, 15])
        self.assertEqual(
            normalize_candles(
                (),
                instrument=Instrument.BANKNIFTY,
                timeframe=Timeframe.M5,
                source_timezone=timezone,
            ),
            (),
        )

        invalid = self._values()
        invalid["volume"] = "fractional"
        with self.assertRaisesRegex(DataNormalizationError, "record 1"):
            normalize_candles(
                (self._values(), invalid, self._values()),
                instrument=Instrument.BANKNIFTY,
                timeframe=Timeframe.M5,
                source_timezone=timezone,
            )

    def test_normalization_error_remains_a_data_engine_error(self) -> None:
        """Keep the dedicated normalization error in the public hierarchy."""
        self.assertTrue(issubclass(DataNormalizationError, DataEngineError))

    @staticmethod
    def _values(*, timestamp: datetime | None = None) -> dict[str, object]:
        """Return provider-independent input values with canonical field names."""
        return {
            "timestamp": timestamp or datetime(2026, 7, 17, 9, 15),
            "open": Decimal("100.25"),
            "high": "101.50",
            "low": 99,
            "close": 100.75,
            "volume": "10",
        }


if __name__ == "__main__":
    unittest.main()
