"""Immutable declarative configuration for provider adapters."""

from dataclasses import dataclass
from zoneinfo import ZoneInfo

from src.engines.data.exceptions import (
    UnsupportedInstrumentError,
    UnsupportedTimeframeError,
)
from src.engines.data.models import Instrument, Timeframe


@dataclass(frozen=True, slots=True)
class ProviderConfig:
    """Describes provider mappings and source timezone without runtime state."""

    provider_name: str
    source_timezone: ZoneInfo
    instrument_codes: tuple[tuple[Instrument, str], ...]
    timeframe_codes: tuple[tuple[Timeframe, str], ...]

    def __post_init__(self) -> None:
        """Reject ambiguous or mutable configuration inputs at construction time."""
        if not isinstance(self.provider_name, str) or not self.provider_name:
            raise ValueError("provider_name must be a non-empty string")
        if not isinstance(self.source_timezone, ZoneInfo):
            raise TypeError("source_timezone must be a ZoneInfo")
        _validate_mappings(self.instrument_codes, Instrument, "instrument_codes")
        _validate_mappings(self.timeframe_codes, Timeframe, "timeframe_codes")

    def instrument_code(self, instrument: Instrument) -> str:
        """Return the provider-specific code for a supported instrument."""
        for configured_instrument, provider_code in self.instrument_codes:
            if configured_instrument is instrument:
                return provider_code
        raise UnsupportedInstrumentError("Requested instrument is unsupported by this provider.")

    def timeframe_code(self, timeframe: Timeframe) -> str:
        """Return the provider-specific code for a supported timeframe."""
        for configured_timeframe, provider_code in self.timeframe_codes:
            if configured_timeframe is timeframe:
                return provider_code
        raise UnsupportedTimeframeError("Requested timeframe is unsupported by this provider.")


def _validate_mappings(
    mappings: tuple[tuple[object, str], ...],
    expected_type: type[Instrument] | type[Timeframe],
    field_name: str,
) -> None:
    """Ensure mappings are immutable, typed, complete key-to-code declarations."""
    if not isinstance(mappings, tuple):
        raise TypeError(f"{field_name} must be a tuple")

    configured_values: set[object] = set()
    for mapping in mappings:
        if not isinstance(mapping, tuple) or len(mapping) != 2:
            raise TypeError(f"{field_name} entries must be two-item tuples")
        canonical_value, provider_code = mapping
        if not isinstance(canonical_value, expected_type):
            raise TypeError(f"{field_name} contains an unsupported canonical value")
        if not isinstance(provider_code, str) or not provider_code:
            raise ValueError(f"{field_name} provider codes must be non-empty strings")
        if canonical_value in configured_values:
            raise ValueError(f"{field_name} cannot contain duplicate canonical values")
        configured_values.add(canonical_value)
