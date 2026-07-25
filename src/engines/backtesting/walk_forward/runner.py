"""Deterministic walk-forward execution over existing injected contracts."""

from dataclasses import dataclass
from typing import Protocol

from src.engines.backtesting.walk_forward.dataset import DatasetWindow
from src.engines.backtesting.walk_forward.execution import (
    WalkForwardSelection,
    WalkForwardTrainer,
    WalkForwardValidationExecutor,
    WalkForwardValidationResult,
)
from src.engines.backtesting.walk_forward.models import WalkForwardPlan, WalkForwardWindow
from src.engines.backtesting.walk_forward.split import (
    TrainingValidationSplitEngine,
    WalkForwardDatasetSplit,
)
from src.engines.data.models import Candle

__all__ = [
    "StandardWalkForwardRunner",
    "WalkForwardIterationResult",
    "WalkForwardRun",
    "WalkForwardRunner",
]


@dataclass(frozen=True, slots=True)
class WalkForwardIterationResult:
    """Record the complete immutable output of one executed plan window."""

    split: WalkForwardDatasetSplit
    selection: WalkForwardSelection
    validation_result: WalkForwardValidationResult

    def __post_init__(self) -> None:
        """Require one internally consistent split, selection, and result."""
        if not isinstance(self.split, WalkForwardDatasetSplit):
            raise TypeError("split must be a WalkForwardDatasetSplit.")
        if not isinstance(self.selection, WalkForwardSelection):
            raise TypeError("selection must be a WalkForwardSelection.")
        if not isinstance(self.validation_result, WalkForwardValidationResult):
            raise TypeError(
                "validation_result must be a WalkForwardValidationResult."
            )
        if self.validation_result.selection != self.selection:
            raise ValueError("validation_result selection must match selection.")
        if self.validation_result.validation_window != self.split.validation:
            raise ValueError(
                "validation_result window must match split validation window."
            )

    @property
    def source_window(self) -> WalkForwardWindow:
        """Return the plan window retained by the complete dataset split."""
        return self.split.source_window

    @property
    def training(self) -> DatasetWindow:
        """Return the training window retained by the complete dataset split."""
        return self.split.training

    @property
    def validation(self) -> DatasetWindow:
        """Return the validation window retained by the complete dataset split."""
        return self.split.validation


@dataclass(frozen=True, slots=True)
class WalkForwardRun:
    """Record ordered complete iteration results for one supplied plan."""

    plan: WalkForwardPlan
    iterations: tuple[WalkForwardIterationResult, ...] = ()

    def __post_init__(self) -> None:
        """Require every plan window to have one same-order iteration result."""
        if not isinstance(self.plan, WalkForwardPlan):
            raise TypeError("plan must be a WalkForwardPlan.")
        if not isinstance(self.iterations, tuple):
            raise TypeError(
                "iterations must be a tuple of WalkForwardIterationResult values."
            )
        if any(
            not isinstance(iteration, WalkForwardIterationResult)
            for iteration in self.iterations
        ):
            raise TypeError(
                "iterations must contain only WalkForwardIterationResult values."
            )
        source_windows = tuple(iteration.source_window for iteration in self.iterations)
        if source_windows != self.plan.windows:
            raise ValueError("iterations must match plan windows in plan order.")


class WalkForwardRunner(Protocol):
    """Define sequential execution of one supplied plan over observations."""

    def run(
        self,
        plan: WalkForwardPlan,
        observations: tuple[Candle, ...],
    ) -> WalkForwardRun:
        """Return complete ordered results without scheduling or partial output."""


@dataclass(frozen=True, slots=True)
class StandardWalkForwardRunner:
    """Compose split, training, and validation collaborators sequentially."""

    split_engine: TrainingValidationSplitEngine
    trainer: WalkForwardTrainer
    validation_executor: WalkForwardValidationExecutor

    def __post_init__(self) -> None:
        """Require injected collaborators without inspecting their structure."""
        if self.split_engine is None:
            raise TypeError("split_engine must not be None.")
        if self.trainer is None:
            raise TypeError("trainer must not be None.")
        if self.validation_executor is None:
            raise TypeError("validation_executor must not be None.")

    def run(
        self,
        plan: WalkForwardPlan,
        observations: tuple[Candle, ...],
    ) -> WalkForwardRun:
        """Execute each supplied plan window in order through injected contracts."""
        if not isinstance(plan, WalkForwardPlan):
            raise TypeError("plan must be a WalkForwardPlan.")
        if not isinstance(observations, tuple):
            raise TypeError("observations must be a tuple of Candle values.")

        iterations: list[WalkForwardIterationResult] = []
        for window in plan.windows:
            split = self.split_engine.split(observations, window)
            if not isinstance(split, WalkForwardDatasetSplit):
                raise TypeError(
                    "split_engine.split must return a WalkForwardDatasetSplit."
                )
            if split.source_window != window:
                raise ValueError("split_engine result must retain the source window.")

            selection = self.trainer.train(split.training)
            if not isinstance(selection, WalkForwardSelection):
                raise TypeError(
                    "trainer.train must return a WalkForwardSelection."
                )

            validation_result = self.validation_executor.validate(
                selection,
                split.validation,
            )
            if not isinstance(validation_result, WalkForwardValidationResult):
                raise TypeError(
                    "validation_executor.validate must return a "
                    "WalkForwardValidationResult."
                )
            iterations.append(
                WalkForwardIterationResult(split, selection, validation_result)
            )

        return WalkForwardRun(plan, tuple(iterations))
