"""Immutable observed-fact models for BANKNIFTY ORB research sessions."""

from dataclasses import dataclass
from datetime import datetime

from src.engines.data.models import Candle, Session

__all__ = ["OpeningRange", "ORBSession", "ORBWindow"]


@dataclass(frozen=True, slots=True)
class ORBWindow:
    """Identifies the canonical timestamp interval observed as an ORB window."""

    start_timestamp: datetime
    end_timestamp: datetime

    def __post_init__(self) -> None:
        """Require timezone-aware, non-descending window timestamps."""
        _require_timezone_aware(self.start_timestamp, "start_timestamp")
        _require_timezone_aware(self.end_timestamp, "end_timestamp")
        if self.end_timestamp < self.start_timestamp:
            raise ValueError("end_timestamp must not precede start_timestamp")


@dataclass(frozen=True, slots=True)
class OpeningRange:
    """Records observed canonical values and evidence for an opening range."""

    window: ORBWindow
    open: float
    high: float
    low: float
    close: float
    candles: tuple[Candle, ...]

    def __post_init__(self) -> None:
        """Require the observed high to be at least the observed low."""
        if self.high < self.low:
            raise ValueError("high must not be below low")


@dataclass(frozen=True, slots=True)
class ORBSession:
    """Associates one canonical session with its observed opening range."""

    session: Session
    opening_range: OpeningRange


def _require_timezone_aware(timestamp: datetime, field_name: str) -> None:
    """Reject timestamps that cannot identify a canonical timezone instant."""
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
