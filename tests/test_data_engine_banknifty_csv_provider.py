"""Tests for the deterministic local BANKNIFTY M5 CSV provider."""

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from zoneinfo import ZoneInfo

from src.engines.data import (
    BankNiftyM5CsvProvider,
    DataEngineExecutionRequest,
    DataEngineExecutionResult,
    DataEngineOrchestrator,
    DataSourceError,
    ExecutionStatus,
    Instrument,
    Timeframe,
    ValidationCode,
)

_HEADER = "timestamp,open,high,low,close,volume\n"
_ROW = "2026-07-17T09:15:00,100,101,99,100.5,10\n"


class BankNiftyM5CsvProviderTests(unittest.TestCase):
    """Verify local CSV parsing and downstream canonical validation ownership."""

    def test_valid_single_row_csv_returns_one_normalized_candle(self) -> None:
        """A canonical source row becomes one immutable BANKNIFTY M5 candle."""
        provider = self._provider(_HEADER + _ROW)

        candles = self._fetch(provider)

        self.assertEqual(len(candles), 1)
        self.assertEqual(candles[0].instrument, Instrument.BANKNIFTY)
        self.assertEqual(candles[0].timeframe, Timeframe.M5)
        self.assertEqual(candles[0].timestamp.tzinfo, ZoneInfo("Asia/Kolkata"))
        self.assertEqual(candles[0].volume, 10)

    def test_valid_multi_row_csv_preserves_source_order_and_date_range(self) -> None:
        """The provider neither reorders rows nor returns other canonical dates."""
        provider = self._provider(
            _HEADER
            + _ROW
            + "2026-07-17T09:20:00,101,102,100,101.5,11\n"
            + "2026-07-18T09:15:00,102,103,101,102.5,12\n"
        )

        candles = self._fetch(provider, end_date=date(2026, 7, 17))

        self.assertEqual([candle.timestamp.minute for candle in candles], [15, 20])

    def test_required_and_extra_columns_are_rejected(self) -> None:
        """CSV schema must form the canonical mapping exactly."""
        missing = self._provider("timestamp,open,high,low,close\n" + _ROW)
        extra = self._provider(
            _HEADER.rstrip() + ",source\n" + _ROW.rstrip() + ",csv\n"
        )

        with self.assertRaises(DataSourceError):
            self._fetch(missing)
        with self.assertRaises(DataSourceError):
            self._fetch(extra)

    def test_duplicate_header_and_empty_or_malformed_sources_are_rejected(self) -> None:
        """Source-level CSV failures stay provider concerns."""
        duplicate = self._provider(
            "timestamp,open,high,low,close,volume,volume\n" + _ROW
        )
        empty = self._provider("")
        header_only = self._provider(_HEADER)
        malformed = self._provider(
            _HEADER + '"2026-07-17T09:15:00,100,101,99,100.5,10\n'
        )

        for provider in (duplicate, empty, header_only, malformed):
            with self.subTest(provider=provider):
                with self.assertRaises(DataSourceError):
                    self._fetch(provider)

    def test_blank_or_incomplete_records_are_rejected(self) -> None:
        """Each record must provide every canonical value to normalization."""
        blank = self._provider(_HEADER + "\n")
        incomplete = self._provider(_HEADER + "2026-07-17T09:15:00,100,101,99,,10\n")

        for provider in (blank, incomplete):
            with self.subTest(provider=provider):
                with self.assertRaises(DataSourceError):
                    self._fetch(provider)

    def test_timestamp_and_numeric_normalization_failures_are_source_errors(
        self,
    ) -> None:
        """Parsing and normalization details cannot cross the source boundary."""
        invalid_timestamp = self._provider(
            _HEADER + "not-a-timestamp,100,101,99,100.5,10\n"
        )
        invalid_numeric = self._provider(
            _HEADER + "2026-07-17T09:15:00,NaN,101,99,100.5,10\n"
        )
        invalid_volume = self._provider(
            _HEADER + "2026-07-17T09:15:00,100,101,99,100.5,1.5\n"
        )
        infinite_price = self._provider(
            _HEADER + "2026-07-17T09:15:00,Infinity,101,99,100.5,10\n"
        )

        for provider in (
            invalid_timestamp,
            invalid_numeric,
            invalid_volume,
            infinite_price,
        ):
            with self.subTest(provider=provider):
                with self.assertRaises(DataSourceError):
                    self._fetch(provider)

    def test_timezone_is_normalized_using_the_declared_source_timezone(self) -> None:
        """Naive CSV timestamps cross the canonical boundary once into market time."""
        provider = self._provider(
            _HEADER + "2026-07-17T03:45:00,100,101,99,100.5,10\n",
            source_timezone=ZoneInfo("UTC"),
        )

        candle = self._fetch(provider)[0]

        self.assertEqual(candle.timestamp.hour, 9)
        self.assertEqual(candle.timestamp.minute, 15)
        self.assertEqual(candle.timestamp.tzinfo, ZoneInfo("Asia/Kolkata"))

    def test_orchestrator_rejects_malformed_ohlc_downstream(self) -> None:
        """OHLC semantics are intentionally owned by canonical validation."""
        result = self._execute(
            _HEADER + "2026-07-17T09:15:00,100,99,98,100.5,10\n"
        )

        self.assertEqual(result.status, ExecutionStatus.REJECTED)
        self.assertIn(ValidationCode.HIGH_BELOW_OPEN, self._validation_codes(result))

    def test_orchestrator_rejects_duplicate_timestamps_downstream(self) -> None:
        """The provider preserves duplicate detection for canonical validation."""
        result = self._execute(_HEADER + _ROW + _ROW)

        self.assertEqual(result.status, ExecutionStatus.REJECTED)
        self.assertIn(
            ValidationCode.DUPLICATE_TIMESTAMP,
            self._validation_codes(result),
        )

    def test_orchestrator_rejects_descending_timestamps_downstream(self) -> None:
        """The provider preserves source order for canonical ordering validation."""
        result = self._execute(
            _HEADER
            + "2026-07-17T09:20:00,100,101,99,100.5,10\n"
            + _ROW
        )

        self.assertEqual(result.status, ExecutionStatus.REJECTED)
        self.assertIn(
            ValidationCode.TIMESTAMP_OUT_OF_ORDER,
            self._validation_codes(result),
        )

    def test_unreadable_or_non_utf8_sources_are_rejected(self) -> None:
        """Local file failures remain deterministic source-boundary failures."""
        missing = BankNiftyM5CsvProvider(
            Path("missing-banknifty.csv"),
            source_timezone=ZoneInfo("Asia/Kolkata"),
        )
        invalid_utf8 = self._provider_bytes(b"\xff\xfe")

        for provider in (missing, invalid_utf8):
            with self.subTest(provider=provider):
                with self.assertRaises(DataSourceError):
                    self._fetch(provider)

    def _provider(
        self,
        content: str,
        *,
        source_timezone: ZoneInfo = ZoneInfo("Asia/Kolkata"),
    ) -> BankNiftyM5CsvProvider:
        """Create a provider backed by a temporary deterministic fixture file."""
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "banknifty.csv"
        path.write_text(content, encoding="utf-8")
        return BankNiftyM5CsvProvider(path, source_timezone=source_timezone)

    def _provider_bytes(self, content: bytes) -> BankNiftyM5CsvProvider:
        """Create a provider backed by an intentionally non-text fixture file."""
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "banknifty.csv"
        path.write_bytes(content)
        return BankNiftyM5CsvProvider(path, source_timezone=ZoneInfo("Asia/Kolkata"))

    def _fetch(
        self,
        provider: BankNiftyM5CsvProvider,
        *,
        end_date: date = date(2026, 7, 17),
    ) -> tuple[object, ...]:
        """Execute a representative provider request."""
        return provider.fetch(
            instrument=Instrument.BANKNIFTY,
            timeframe=Timeframe.M5,
            start_date=date(2026, 7, 17),
            end_date=end_date,
        )

    def _execute(self, content: str) -> DataEngineExecutionResult:
        """Run the canonical orchestration path for an adapter fixture."""
        return DataEngineOrchestrator().execute(
            self._provider(content),
            self._request(),
        )

    @staticmethod
    def _validation_codes(result: DataEngineExecutionResult) -> set[ValidationCode]:
        """Return canonical validation codes without inspecting source CSV rows."""
        return {
            issue.code
            for validation in result.validation_results
            for issue in validation.issues
        }

    @staticmethod
    def _request() -> DataEngineExecutionRequest:
        """Create an orchestration request spanning the test source records."""
        return DataEngineExecutionRequest(
            instrument=Instrument.BANKNIFTY,
            timeframe=Timeframe.M5,
            start_date=date(2026, 7, 17),
            end_date=date(2026, 7, 17),
        )


if __name__ == "__main__":
    unittest.main()
