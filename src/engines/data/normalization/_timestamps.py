"""Private timestamp conversion helpers for canonical candle normalization."""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from src.engines.data.exceptions import DataNormalizationError

_MARKET_TIMEZONE = ZoneInfo("Asia/Kolkata")


def normalize_timestamp(
    value: object,
    *,
    source_timezone: ZoneInfo,
    record_index: int | None,
) -> datetime:
    """Convert a datetime to an aware ``Asia/Kolkata`` timestamp.

    Provider adapters own source-specific timestamp parsing. This function
    accepts only ``datetime`` instances with an explicit source timezone for
    naive values.
    """
    if not isinstance(value, datetime):
        raise DataNormalizationError(_message("timestamp must be a datetime", record_index))
    if not isinstance(source_timezone, ZoneInfo):
        raise DataNormalizationError(_message("source timezone must be a ZoneInfo", record_index))

    if value.tzinfo is None or value.utcoffset() is None:
        value = _localize_naive(value, source_timezone, record_index=record_index)
    return value.astimezone(_MARKET_TIMEZONE)


def _localize_naive(
    value: datetime,
    source_timezone: ZoneInfo,
    *,
    record_index: int | None,
) -> datetime:
    """Attach an unambiguous source timezone to a naive local timestamp."""
    candidates = []
    for fold in (0, 1):
        candidate = value.replace(tzinfo=source_timezone, fold=fold)
        round_trip = candidate.astimezone(UTC).astimezone(source_timezone)
        if round_trip.replace(tzinfo=None) == value:
            candidates.append(candidate)

    if not candidates:
        raise DataNormalizationError(
            _message("timestamp is nonexistent in source timezone", record_index)
        )
    if len(candidates) == 2 and candidates[0].utcoffset() != candidates[1].utcoffset():
        raise DataNormalizationError(
            _message("timestamp is ambiguous in source timezone", record_index)
        )
    return candidates[0]


def _message(reason: str, record_index: int | None) -> str:
    """Build a deterministic message without exposing provider values."""
    if record_index is None:
        return f"Cannot normalize candle: {reason}."
    return f"Cannot normalize candle at record {record_index}: {reason}."
