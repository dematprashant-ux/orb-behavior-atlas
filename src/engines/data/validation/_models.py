"""Immutable public result types for canonical candle validation."""

from dataclasses import dataclass
from enum import Enum

from src.engines.data.models import Candle


class ValidationSeverity(str, Enum):
    """Classifies the impact of a canonical validation finding."""

    ERROR = "ERROR"
    WARNING = "WARNING"


class ValidationCode(str, Enum):
    """Identifies one stable category of canonical candle validation issue."""

    UNSUPPORTED_INSTRUMENT = "UNSUPPORTED_INSTRUMENT"
    UNSUPPORTED_TIMEFRAME = "UNSUPPORTED_TIMEFRAME"
    TIMESTAMP_NAIVE = "TIMESTAMP_NAIVE"
    TIMESTAMP_NOT_ASIA_KOLKATA = "TIMESTAMP_NOT_ASIA_KOLKATA"
    SESSION_DATE_MISMATCH = "SESSION_DATE_MISMATCH"
    NEGATIVE_PRICE = "NEGATIVE_PRICE"
    HIGH_BELOW_OPEN = "HIGH_BELOW_OPEN"
    HIGH_BELOW_CLOSE = "HIGH_BELOW_CLOSE"
    HIGH_BELOW_LOW = "HIGH_BELOW_LOW"
    LOW_ABOVE_OPEN = "LOW_ABOVE_OPEN"
    LOW_ABOVE_CLOSE = "LOW_ABOVE_CLOSE"
    NEGATIVE_VOLUME = "NEGATIVE_VOLUME"
    DUPLICATE_TIMESTAMP = "DUPLICATE_TIMESTAMP"
    TIMESTAMP_OUT_OF_ORDER = "TIMESTAMP_OUT_OF_ORDER"


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """Describes one deterministic semantic candle validation finding."""

    code: ValidationCode
    severity: ValidationSeverity
    message: str
    field: str | None
    related_index: int | None
    rule_id: str | None = None


@dataclass(frozen=True, slots=True)
class CandleValidationResult:
    """Pairs one immutable candle with its ordered validation issues."""

    candle: Candle
    issues: tuple[ValidationIssue, ...]

    @property
    def is_valid(self) -> bool:
        """Return whether this result contains no error-severity issue."""
        return not any(issue.severity is ValidationSeverity.ERROR for issue in self.issues)
