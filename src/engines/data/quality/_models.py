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
