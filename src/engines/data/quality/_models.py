"""Immutable public models for read-only canonical data-quality assessment."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from src.engines.data.models import Session


class QualitySeverity(str, Enum):
    """Classifies the impact of an observational data-quality finding."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class QualityCode(str, Enum):
    """Identifies a stable category of observational quality finding."""

    UNEXPECTED_INTERVAL = "UNEXPECTED_INTERVAL"


class MarketSessionQualityStatus(str, Enum):
    """Classifies a session's deterministic suitability for market research."""

    VALID_COMPLETE_SESSION = "VALID_COMPLETE_SESSION"
    VALID_PARTIAL_SESSION = "VALID_PARTIAL_SESSION"
    REJECTED_SESSION = "REJECTED_SESSION"


class MarketSessionRejectionCode(str, Enum):
    """Identifies stable reasons a session cannot pass market-quality checks."""

    EMPTY_SESSION = "EMPTY_SESSION"
    CANDLE_VALIDATION = "CANDLE_VALIDATION"
    OUTSIDE_REGULAR_SESSION = "OUTSIDE_REGULAR_SESSION"
    UNALIGNED_M5_TIMESTAMP = "UNALIGNED_M5_TIMESTAMP"
    INTERNAL_M5_GAP = "INTERNAL_M5_GAP"


@dataclass(frozen=True, slots=True)
class QualityIssue:
    """Describes one immutable observation without embedding candle objects."""

    code: QualityCode
    severity: QualitySeverity
    message: str
    previous_timestamp: datetime
    current_timestamp: datetime
    expected_interval: timedelta
    observed_interval: timedelta


@dataclass(frozen=True, slots=True)
class SessionQualityMetrics:
    """Summarizes read-only observations for one supplied session."""

    candle_count: int
    unexpected_interval_count: int
    first_timestamp: datetime | None
    last_timestamp: datetime | None


@dataclass(frozen=True, slots=True)
class SessionQualityResult:
    """Pairs one supplied session with ordered quality observations."""

    session: Session
    metrics: SessionQualityMetrics
    issues: tuple[QualityIssue, ...]


@dataclass(frozen=True, slots=True)
class DataQualityReport:
    """Groups immutable quality results while preserving supplied session order."""

    sessions: tuple[SessionQualityResult, ...]

    @property
    def session_count(self) -> int:
        """Return the number of assessed sessions."""
        return len(self.sessions)

    @property
    def candle_count(self) -> int:
        """Return the total number of observed candles."""
        return sum(result.metrics.candle_count for result in self.sessions)

    @property
    def unexpected_interval_count(self) -> int:
        """Return the total number of observed unexpected intervals."""
        return sum(result.metrics.unexpected_interval_count for result in self.sessions)


@dataclass(frozen=True, slots=True)
class MarketSessionRejection:
    """Describes one stable market-quality rejection without mutating a session."""

    code: MarketSessionRejectionCode
    detail: str | None = None

    def __post_init__(self) -> None:
        """Keep rejection facts typed and concise for deterministic audit output."""
        if not isinstance(self.code, MarketSessionRejectionCode):
            raise TypeError("code must be a MarketSessionRejectionCode")
        if self.detail is not None and not isinstance(self.detail, str):
            raise TypeError("detail must be a string or None")


@dataclass(frozen=True, slots=True)
class MarketSessionQualityResult:
    """Pairs one supplied session with its complete, partial, or rejected outcome."""

    session: Session
    status: MarketSessionQualityStatus
    rejections: tuple[MarketSessionRejection, ...]

    def __post_init__(self) -> None:
        """Require outcomes to retain their session and match rejection semantics."""
        if not isinstance(self.session, Session):
            raise TypeError("session must be a Session")
        if not isinstance(self.status, MarketSessionQualityStatus):
            raise TypeError("status must be a MarketSessionQualityStatus")
        if not isinstance(self.rejections, tuple):
            raise TypeError("rejections must be a tuple")
        if any(
            not isinstance(item, MarketSessionRejection)
            for item in self.rejections
        ):
            raise TypeError("rejections must contain MarketSessionRejection values")
        if self.status is MarketSessionQualityStatus.REJECTED_SESSION:
            if not self.rejections:
                raise ValueError("a rejected session requires at least one rejection")
        elif self.rejections:
            raise ValueError("a valid session cannot contain rejections")
