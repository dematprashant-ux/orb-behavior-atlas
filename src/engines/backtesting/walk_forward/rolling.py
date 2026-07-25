"""Deterministic rolling walk-forward schedule generation without dataset access."""

from dataclasses import dataclass
from datetime import timedelta
from typing import Protocol

from src.engines.backtesting.walk_forward.models import (
    DateTimeRange,
    WalkForwardPlan,
    WalkForwardWindow,
)

__all__ = [
    "RollingWindowGenerator",
    "StandardRollingWindowGenerator",
    "WalkForwardConfiguration",
]


@dataclass(frozen=True, slots=True)
class WalkForwardConfiguration:
    """Defines one explicit rolling schedule using actual datetime durations."""

    overall_range: DateTimeRange
    training_duration: timedelta
    validation_duration: timedelta
    step_duration: timedelta

    def __post_init__(self) -> None:
        if not isinstance(self.overall_range, DateTimeRange):
            raise TypeError("overall_range must be a DateTimeRange.")
        for value, name in (
            (self.training_duration, "training_duration"),
            (self.validation_duration, "validation_duration"),
            (self.step_duration, "step_duration"),
        ):
            if not isinstance(value, timedelta):
                raise TypeError(f"{name} must be a timedelta.")
            if value <= timedelta(0):
                raise ValueError(f"{name} must be positive.")


class RollingWindowGenerator(Protocol):
    """Defines pure construction of chronological rolling walk-forward plans."""

    def generate(self, configuration: WalkForwardConfiguration) -> WalkForwardPlan:
        """Return complete windows only, without dataset or calendar awareness."""


@dataclass(frozen=True, slots=True)
class StandardRollingWindowGenerator:
    """Generate fixed-duration rolling training and validation ranges."""

    def generate(self, configuration: WalkForwardConfiguration) -> WalkForwardPlan:
        """Build complete half-open windows in chronological anchor order."""
        if not isinstance(configuration, WalkForwardConfiguration):
            raise TypeError("configuration must be a WalkForwardConfiguration.")
        windows: list[WalkForwardWindow] = []
        anchor = configuration.overall_range.start
        while True:
            training_end = anchor + configuration.training_duration
            validation_end = training_end + configuration.validation_duration
            if validation_end > configuration.overall_range.end:
                break
            windows.append(
                WalkForwardWindow(
                    len(windows),
                    DateTimeRange(anchor, training_end),
                    DateTimeRange(training_end, validation_end),
                )
            )
            anchor += configuration.step_duration
        return WalkForwardPlan(tuple(windows))
