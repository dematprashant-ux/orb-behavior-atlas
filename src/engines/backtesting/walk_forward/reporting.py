"""Immutable walk-forward reporting values and deterministic orchestration."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol

from src.engines.backtesting.walk_forward.models import WalkForwardPlan
from src.engines.backtesting.walk_forward.rolling import (
    RollingWindowGenerator,
    WalkForwardConfiguration,
)
from src.engines.backtesting.walk_forward.runner import (
    WalkForwardRun,
    WalkForwardRunner,
)
from src.engines.data.models import Candle

__all__ = [
    "StandardWalkForwardAnalyticsPipeline",
    "StandardWalkForwardReportBuilder",
    "WalkForwardAnalyticsPipeline",
    "WalkForwardReport",
    "WalkForwardReportBuilder",
    "WalkForwardReportType",
    "WalkForwardStructuralSummary",
]


class WalkForwardReportType(str, Enum):
    """Identify the canonical report representation without presentation logic."""

    WALK_FORWARD = "walk_forward"


@dataclass(frozen=True, slots=True)
class WalkForwardStructuralSummary:
    """Record deterministic structural facts already present in a run plan."""

    total_windows: int
    completed_iterations: int
    earliest_training_start: datetime | None
    latest_validation_end: datetime | None

    def __post_init__(self) -> None:
        """Require non-negative counts and paired chronological boundaries."""
        for value, name in (
            (self.total_windows, "total_windows"),
            (self.completed_iterations, "completed_iterations"),
        ):
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an int.")
            if value < 0:
                raise ValueError(f"{name} must be non-negative.")
        if (self.earliest_training_start is None) != (
            self.latest_validation_end is None
        ):
            raise ValueError("summary boundaries must both be known or unknown.")
        if self.earliest_training_start is not None:
            _aware(self.earliest_training_start, "earliest_training_start")
            _aware(self.latest_validation_end, "latest_validation_end")
            if self.earliest_training_start > self.latest_validation_end:
                raise ValueError("summary start must not follow summary end.")


@dataclass(frozen=True, slots=True)
class WalkForwardReport:
    """Compose a completed run and its structural representation by reference."""

    run: WalkForwardRun
    summary: WalkForwardStructuralSummary
    report_type: WalkForwardReportType = WalkForwardReportType.WALK_FORWARD

    def __post_init__(self) -> None:
        """Require a typed run, matching structural summary, and report identity."""
        if not isinstance(self.run, WalkForwardRun):
            raise TypeError("run must be a WalkForwardRun.")
        if not isinstance(self.summary, WalkForwardStructuralSummary):
            raise TypeError("summary must be a WalkForwardStructuralSummary.")
        if not isinstance(self.report_type, WalkForwardReportType):
            raise TypeError("report_type must be a WalkForwardReportType.")
        if self.summary.total_windows != len(self.run.plan.windows):
            raise ValueError("summary total_windows must match the run plan.")
        if self.summary.completed_iterations != len(self.run.iterations):
            raise ValueError("summary completed_iterations must match the run.")


class WalkForwardReportBuilder(Protocol):
    """Define pure construction of a report from an existing walk-forward run."""

    def build(self, run: WalkForwardRun) -> WalkForwardReport:
        """Return an immutable report without execution, rendering, or I/O."""


@dataclass(frozen=True, slots=True)
class StandardWalkForwardReportBuilder:
    """Build structural report facts without analytics or presentation work."""

    def build(self, run: WalkForwardRun) -> WalkForwardReport:
        """Compose one report with deterministic plan-derived summary values."""
        if not isinstance(run, WalkForwardRun):
            raise TypeError("run must be a WalkForwardRun.")
        windows = run.plan.windows
        if not windows:
            boundaries: tuple[datetime | None, datetime | None] = (None, None)
        else:
            boundaries = (
                min(window.training_range.start for window in windows),
                max(window.validation_range.end for window in windows),
            )
        return WalkForwardReport(
            run=run,
            summary=WalkForwardStructuralSummary(
                total_windows=len(windows),
                completed_iterations=len(run.iterations),
                earliest_training_start=boundaries[0],
                latest_validation_end=boundaries[1],
            ),
        )


class WalkForwardAnalyticsPipeline(Protocol):
    """Define deterministic planning, execution, and report composition."""

    def run(
        self,
        configuration: WalkForwardConfiguration,
        observations: tuple[Candle, ...],
    ) -> WalkForwardReport:
        """Return one report without analytics, serialization, rendering, or I/O."""


@dataclass(frozen=True, slots=True)
class StandardWalkForwardAnalyticsPipeline:
    """Coordinate injected plan generation, run execution, and report building."""

    rolling_window_generator: RollingWindowGenerator
    walk_forward_runner: WalkForwardRunner
    report_builder: WalkForwardReportBuilder

    def __post_init__(self) -> None:
        """Require injected collaborators without structural reflection."""
        for collaborator, name in (
            (self.rolling_window_generator, "rolling_window_generator"),
            (self.walk_forward_runner, "walk_forward_runner"),
            (self.report_builder, "report_builder"),
        ):
            if collaborator is None:
                raise TypeError(f"{name} must not be None.")

    def run(
        self,
        configuration: WalkForwardConfiguration,
        observations: tuple[Candle, ...],
    ) -> WalkForwardReport:
        """Delegate once in deterministic order and propagate all failures."""
        if not isinstance(configuration, WalkForwardConfiguration):
            raise TypeError("configuration must be a WalkForwardConfiguration.")
        if not isinstance(observations, tuple):
            raise TypeError("observations must be a tuple of Candle values.")
        plan = self.rolling_window_generator.generate(configuration)
        if not isinstance(plan, WalkForwardPlan):
            raise TypeError(
                "rolling_window_generator.generate must return a WalkForwardPlan."
            )
        run = self.walk_forward_runner.run(plan, observations)
        if not isinstance(run, WalkForwardRun):
            raise TypeError("walk_forward_runner.run must return a WalkForwardRun.")
        if run.plan != plan:
            raise ValueError("walk_forward_runner result must retain the plan.")
        report = self.report_builder.build(run)
        if not isinstance(report, WalkForwardReport):
            raise TypeError("report_builder.build must return a WalkForwardReport.")
        if report.run != run:
            raise ValueError("report_builder result must retain the run.")
        return report


def _aware(value: datetime | None, field_name: str) -> None:
    """Require a timezone-aware report boundary from an existing plan."""
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime.")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware.")
