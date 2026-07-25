"""Immutable half-open interval and walk-forward planning domain values."""

from dataclasses import dataclass
from datetime import datetime

__all__ = ["DateTimeRange", "WalkForwardPlan", "WalkForwardWindow"]


@dataclass(frozen=True, slots=True)
class DateTimeRange:
    """Represents the explicit chronological half-open interval ``[start, end)``."""

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        _aware(self.start, "start")
        _aware(self.end, "end")
        if self.start >= self.end:
            raise ValueError("start must be before end.")

    def contains(self, timestamp: datetime) -> bool:
        """Return whether a timestamp belongs to this half-open range."""
        _aware(timestamp, "timestamp")
        return self.start <= timestamp < self.end


@dataclass(frozen=True, slots=True)
class WalkForwardWindow:
    """Records one deterministic training and validation range pair."""

    index: int
    training_range: DateTimeRange
    validation_range: DateTimeRange

    def __post_init__(self) -> None:
        if isinstance(self.index, bool) or not isinstance(self.index, int):
            raise TypeError("index must be an int.")
        if self.index < 0:
            raise ValueError("index must be non-negative.")
        if not isinstance(self.training_range, DateTimeRange):
            raise TypeError("training_range must be a DateTimeRange.")
        if not isinstance(self.validation_range, DateTimeRange):
            raise TypeError("validation_range must be a DateTimeRange.")
        if self.training_range.end > self.validation_range.start:
            raise ValueError("training and validation ranges must not overlap.")


@dataclass(frozen=True, slots=True)
class WalkForwardPlan:
    """Records an ordered immutable collection of unique windows."""

    windows: tuple[WalkForwardWindow, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.windows, tuple):
            raise TypeError("windows must be a tuple of WalkForwardWindow values.")
        if any(not isinstance(window, WalkForwardWindow) for window in self.windows):
            raise TypeError("windows must contain only WalkForwardWindow values.")
        indices = tuple(window.index for window in self.windows)
        if len(indices) != len(set(indices)):
            raise ValueError("windows must not contain duplicate indices.")
        if any(
            current.training_range.start <= previous.training_range.start
            for previous, current in zip(self.windows, self.windows[1:])
        ):
            raise ValueError("windows must be in increasing training chronology.")


def _aware(value: datetime, field_name: str) -> None:
    """Require aware datetimes without calendar or dataset interpretation."""
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime.")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware.")
