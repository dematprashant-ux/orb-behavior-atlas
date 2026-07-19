"""Contract tests for the transport-neutral provider adapter framework."""

from dataclasses import FrozenInstanceError, is_dataclass
from datetime import date, datetime
from inspect import Parameter, signature
import unittest
from zoneinfo import ZoneInfo

from src.engines.data import (
    BaseProviderAdapter,
    Candle,
    DataNormalizationError,
    DataSource,
    DataSourceError,
    Instrument,
    ProviderAdapter,
    ProviderConfig,
    Timeframe,
    UnsupportedInstrumentError,
    UnsupportedTimeframeError,
)


class DataEngineProviderContractTests(unittest.TestCase):
    """Verify provider mapping and normalization without concrete provider behavior."""

    def test_public_adapter_contract_preserves_data_source_fetch_signature(self) -> None:
        """Keep DataSource.fetch as the sole public retrieval operation."""
        self.assertEqual(
            list(signature(BaseProviderAdapter.fetch).parameters),
            list(signature(DataSource.fetch).parameters),
        )
        self.assertTrue(ProviderAdapter)
        self.assertNotIn("fetch_with_validation", dir(ProviderAdapter))

    def test_config_is_immutable_and_resolves_canonical_request_codes(self) -> None:
        """Keep declarative mappings free of runtime state and mutable members."""
        config = self._config()
        self.assertTrue(is_dataclass(config))
        self.assertEqual(config.instrument_code(Instrument.BANKNIFTY), "BANKNIFTY_INDEX")
        self.assertEqual(config.timeframe_code(Timeframe.M5), "5m")
        with self.assertRaises(FrozenInstanceError):
            config.provider_name = "changed"

    def test_unsupported_requests_raise_existing_data_engine_exceptions(self) -> None:
        """Reject absent mappings without introducing provider-specific exceptions."""
        config = ProviderConfig(
            provider_name="fake",
            source_timezone=ZoneInfo("UTC"),
            instrument_codes=(),
            timeframe_codes=(),
        )
        with self.assertRaises(UnsupportedInstrumentError):
            config.instrument_code(Instrument.BANKNIFTY)
        with self.assertRaises(UnsupportedTimeframeError):
            config.timeframe_code(Timeframe.M5)

    def test_base_adapter_maps_parses_and_normalizes_payloads(self) -> None:
        """Return ordered canonical candles after provider-specific parsing."""
        adapter = _FakeAdapter(self._config(), payloads=(self._payload(),))

        candles = adapter.fetch(
            instrument=Instrument.BANKNIFTY,
            timeframe=Timeframe.M5,
            start_date=date(2026, 7, 17),
            end_date=date(2026, 7, 17),
        )

        self.assertEqual(adapter.request, ("BANKNIFTY_INDEX", "5m"))
        self.assertEqual(len(candles), 1)
        self.assertIsInstance(candles[0], Candle)
        self.assertEqual(candles[0].timestamp.tzinfo, ZoneInfo("Asia/Kolkata"))
        self.assertEqual(candles[0].session_date, date(2026, 7, 17))

    def test_adapter_returns_semantically_invalid_candles_without_validation(self) -> None:
        """Keep M2.5 validation execution outside the adapter responsibility."""
        payload = self._payload()
        payload["h"] = 99.0
        adapter = _FakeAdapter(self._config(), payloads=(payload,))

        candles = adapter.fetch(
            instrument=Instrument.BANKNIFTY,
            timeframe=Timeframe.M5,
            start_date=date(2026, 7, 17),
            end_date=date(2026, 7, 17),
        )

        self.assertEqual(candles[0].high, 99.0)

    def test_provider_parse_and_normalization_failures_are_safe_source_errors(self) -> None:
        """Hide provider details while retaining internal causes for diagnosis."""
        parsing_adapter = _FakeAdapter(
            self._config(),
            payloads=(self._payload(),),
            parse_error=ValueError("provider-secret"),
        )
        normalization_adapter = _FakeAdapter(
            self._config(),
            payloads=(
                {
                    "time": datetime(2026, 7, 17, 9, 15),
                    "o": 100.0,
                    "h": 101.0,
                    "l": 99.0,
                    "c": 100.5,
                    "v": "invalid",
                },
            ),
        )

        with self.assertRaises(DataSourceError) as parsing_error:
            self._fetch(parsing_adapter)
        self.assertNotIn("provider-secret", str(parsing_error.exception))
        self.assertIsInstance(parsing_error.exception.__cause__, ValueError)

        with self.assertRaises(DataSourceError) as normalization_error:
            self._fetch(normalization_adapter)
        self.assertIsInstance(normalization_error.exception.__cause__, DataNormalizationError)

    def test_close_is_a_safe_no_op_without_transport_resources(self) -> None:
        """Allow lifecycle cleanup before concrete resource ownership exists."""
        adapter = _FakeAdapter(self._config(), payloads=())
        self.assertIsNone(adapter.close())

    def _fetch(self, adapter: BaseProviderAdapter) -> None:
        """Invoke a representative inclusive source request."""
        adapter.fetch(
            instrument=Instrument.BANKNIFTY,
            timeframe=Timeframe.M5,
            start_date=date(2026, 7, 17),
            end_date=date(2026, 7, 17),
        )

    @staticmethod
    def _config() -> ProviderConfig:
        """Return immutable configuration for a transport-free fake provider."""
        return ProviderConfig(
            provider_name="fake",
            source_timezone=ZoneInfo("UTC"),
            instrument_codes=((Instrument.BANKNIFTY, "BANKNIFTY_INDEX"),),
            timeframe_codes=((Timeframe.M5, "5m"),),
        )

    @staticmethod
    def _payload() -> dict[str, object]:
        """Return a provider-native payload accepted by the fake parser."""
        return {
            "time": datetime(2026, 7, 17, 3, 45),
            "o": 100.0,
            "h": 101.0,
            "l": 99.0,
            "c": 100.5,
            "v": 1,
        }


class _FakeAdapter(BaseProviderAdapter):
    """Transport-free test adapter that supplies payloads from memory."""

    def __init__(
        self,
        config: ProviderConfig,
        *,
        payloads: tuple[dict[str, object], ...],
        parse_error: Exception | None = None,
    ) -> None:
        """Configure deterministic provider payload behavior for contract tests."""
        super().__init__(config)
        self._payloads = payloads
        self._parse_error = parse_error
        self.request: tuple[str, str] | None = None

    def _fetch_payloads(
        self,
        *,
        provider_instrument: str,
        provider_timeframe: str,
        start_date: date,
        end_date: date,
    ) -> tuple[dict[str, object], ...]:
        """Return configured in-memory payloads without external communication."""
        self.request = (provider_instrument, provider_timeframe)
        return self._payloads

    def _parse_payload(self, payload: object) -> dict[str, object]:
        """Map fake provider aliases to canonical normalization keys."""
        if self._parse_error is not None:
            raise self._parse_error
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dictionary")
        return {
            "timestamp": payload["time"],
            "open": payload["o"],
            "high": payload["h"],
            "low": payload["l"],
            "close": payload["c"],
            "volume": payload["v"],
        }


if __name__ == "__main__":
    unittest.main()
