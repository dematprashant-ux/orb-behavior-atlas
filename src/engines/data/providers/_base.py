"""Reusable transport-neutral orchestration for provider adapters."""

from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping, Sequence
from datetime import date

from src.engines.data.exceptions import DataNormalizationError, DataSourceError
from src.engines.data.models import Candle, Instrument, Timeframe
from src.engines.data.normalization import normalize_candles
from src.engines.data.providers._config import ProviderConfig


class BaseProviderAdapter(ABC):
    """Maps provider input into canonical candles without validation or transport logic."""

    def __init__(self, config: ProviderConfig) -> None:
        """Create an adapter with immutable declarative provider configuration."""
        if not isinstance(config, ProviderConfig):
            raise TypeError("config must be a ProviderConfig")
        self._config = config

    @property
    def config(self) -> ProviderConfig:
        """Return immutable configuration without exposing mutable runtime state."""
        return self._config

    def fetch(
        self,
        *,
        instrument: Instrument,
        timeframe: Timeframe,
        start_date: date,
        end_date: date,
    ) -> Sequence[Candle]:
        """Return normalized canonical candles for an inclusive provider date range."""
        provider_instrument = self._config.instrument_code(instrument)
        provider_timeframe = self._config.timeframe_code(timeframe)
        values = self._canonical_values(
            provider_instrument=provider_instrument,
            provider_timeframe=provider_timeframe,
            start_date=start_date,
            end_date=end_date,
        )
        try:
            return normalize_candles(
                values,
                instrument=instrument,
                timeframe=timeframe,
                source_timezone=self._config.source_timezone,
            )
        except DataNormalizationError as error:
            raise DataSourceError("Provider data could not be normalized.") from error

    def close(self) -> None:
        """Provide an idempotent lifecycle hook without transport implementation."""

    @abstractmethod
    def _fetch_payloads(
        self,
        *,
        provider_instrument: str,
        provider_timeframe: str,
        start_date: date,
        end_date: date,
    ) -> Iterable[object]:
        """Acquire provider-native payloads through a future concrete transport."""

    @abstractmethod
    def _parse_payload(self, payload: object) -> Mapping[str, object]:
        """Parse one payload into canonical keys and provider-independent values."""

    def _canonical_values(
        self,
        *,
        provider_instrument: str,
        provider_timeframe: str,
        start_date: date,
        end_date: date,
    ) -> tuple[Mapping[str, object], ...]:
        """Acquire and parse payloads while preventing provider errors from crossing."""
        try:
            return tuple(
                self._parse_payload(payload)
                for payload in self._fetch_payloads(
                    provider_instrument=provider_instrument,
                    provider_timeframe=provider_timeframe,
                    start_date=start_date,
                    end_date=end_date,
                )
            )
        except DataSourceError:
            raise
        except Exception as error:
            raise DataSourceError("Provider payload could not be acquired or parsed.") from error
