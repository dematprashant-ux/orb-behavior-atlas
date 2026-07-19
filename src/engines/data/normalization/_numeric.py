"""Private numeric coercion helpers for canonical candle normalization."""

from decimal import Decimal, InvalidOperation
from math import isfinite
import re

from src.engines.data.exceptions import DataNormalizationError

_INTEGER_PATTERN = re.compile(r"[+-]?\d+")


def normalize_price(value: object, *, field: str, record_index: int | None) -> float:
    """Convert one finite provider-independent OHLC value to ``float``."""
    decimal_value = _as_finite_decimal(value, field=field, record_index=record_index)
    normalized_value = float(decimal_value)
    if not isfinite(normalized_value):
        raise DataNormalizationError(_message(field, "must be finite", record_index))
    return normalized_value


def normalize_volume(value: object, *, record_index: int | None) -> int:
    """Convert one integral provider-independent volume value to ``int``."""
    if isinstance(value, bool):
        raise DataNormalizationError(_message("volume", "must be an integer", record_index))
    if isinstance(value, float) or not isinstance(value, (int, Decimal, str)):
        raise DataNormalizationError(_message("volume", "must be an integer", record_index))

    if isinstance(value, str) and not _INTEGER_PATTERN.fullmatch(value):
        raise DataNormalizationError(_message("volume", "must be an integer", record_index))

    decimal_value = _as_finite_decimal(value, field="volume", record_index=record_index)
    if decimal_value != decimal_value.to_integral_value():
        raise DataNormalizationError(_message("volume", "must be an integer", record_index))
    return int(decimal_value)


def _as_finite_decimal(value: object, *, field: str, record_index: int | None) -> Decimal:
    """Return a finite decimal or raise a safe, deterministic error."""
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal, str)):
        raise DataNormalizationError(
            _message(field, "must be a finite numeric value", record_index)
        )
    if isinstance(value, str) and not value.strip():
        raise DataNormalizationError(
            _message(field, "must be a finite numeric value", record_index)
        )

    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise DataNormalizationError(
            _message(field, "must be a finite numeric value", record_index)
        ) from error

    if not decimal_value.is_finite():
        raise DataNormalizationError(
            _message(field, "must be a finite numeric value", record_index)
        )
    return decimal_value


def _message(field: str, reason: str, record_index: int | None) -> str:
    """Build a deterministic message without exposing provider values."""
    if record_index is None:
        return f"Cannot normalize candle: field '{field}' {reason}."
    return f"Cannot normalize candle at record {record_index}: field '{field}' {reason}."
