"""Provider-independent conversion into canonical candle models."""

from collections.abc import Iterable, Mapping
from datetime import datetime
from zoneinfo import ZoneInfo

from src.engines.data.exceptions import DataNormalizationError
from src.engines.data.models import Candle, Instrument, Timeframe
from src.engines.data.normalization._numeric import normalize_price, normalize_volume
from src.engines.data.normalization._timestamps import normalize_timestamp

_REQUIRED_FIELDS = ("timestamp", "open", "high", "low", "close", "volume")


def normalize_candle(
    values: Mapping[str, object],
    *,
    instrument: Instrument,
    timeframe: Timeframe,
    source_timezone: ZoneInfo,
) -> Candle:
    """Build a canonical candle from provider-independent candle values.

    Provider adapters must parse provider-native payloads and map their field
    names to the canonical keys before calling this function.
    """
    return _normalize_candle(
        values,
        instrument=instrument,
        timeframe=timeframe,
        source_timezone=source_timezone,
        record_index=None,
    )


def normalize_candles(
    values: Iterable[Mapping[str, object]],
    *,
    instrument: Instrument,
    timeframe: Timeframe,
    source_timezone: ZoneInfo,
) -> tuple[Candle, ...]:
    """Normalize provider-independent candle values in their supplied order.

    The operation is fail-fast. An invalid record raises
    :class:`DataNormalizationError` with its zero-based index.
    """
    return tuple(
        _normalize_candle(
            record,
            instrument=instrument,
            timeframe=timeframe,
            source_timezone=source_timezone,
            record_index=index,
        )
        for index, record in enumerate(values)
    )


def _normalize_candle(
    values: Mapping[str, object],
    *,
    instrument: Instrument,
    timeframe: Timeframe,
    source_timezone: ZoneInfo,
    record_index: int | None,
) -> Candle:
    _require_fields(values, record_index=record_index)

    timestamp = normalize_timestamp(
        values["timestamp"],
        source_timezone=source_timezone,
        record_index=record_index,
    )
    return Candle(
        instrument=instrument,
        timeframe=timeframe,
        timestamp=timestamp,
        session_date=timestamp.date(),
        open=normalize_price(values["open"], field="open", record_index=record_index),
        high=normalize_price(values["high"], field="high", record_index=record_index),
        low=normalize_price(values["low"], field="low", record_index=record_index),
        close=normalize_price(values["close"], field="close", record_index=record_index),
        volume=normalize_volume(values["volume"], record_index=record_index),
    )


def _require_fields(values: Mapping[str, object], *, record_index: int | None) -> None:
    """Ensure all canonical input fields are available without exposing values."""
    for field in _REQUIRED_FIELDS:
        if field not in values:
            raise DataNormalizationError(
                _message(f"missing required field '{field}'", record_index)
            )


def _message(reason: str, record_index: int | None) -> str:
    """Build a deterministic public error message without payload contents."""
    if record_index is None:
        return f"Cannot normalize candle: {reason}."
    return f"Cannot normalize candle at record {record_index}: {reason}."
