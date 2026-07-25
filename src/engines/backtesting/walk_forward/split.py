"""Pure composition of one walk-forward window into dataset selections."""

from dataclasses import dataclass
from typing import Protocol

from src.engines.backtesting.walk_forward.dataset import (
    DatasetWindow,
    DatasetWindowBuilder,
)
from src.engines.backtesting.walk_forward.models import WalkForwardWindow
from src.engines.data.models import Candle

__all__ = [
    "StandardTrainingValidationSplitEngine",
    "TrainingValidationSplitEngine",
    "WalkForwardDatasetSplit",
]


@dataclass(frozen=True, slots=True)
class WalkForwardDatasetSplit:
    """References one source window and its training and validation selections."""

    source_window: WalkForwardWindow
    training: DatasetWindow
    validation: DatasetWindow

    def __post_init__(self) -> None:
        if not isinstance(self.source_window, WalkForwardWindow):
            raise TypeError(
                "source_window must be a WalkForwardWindow."
            )
        if not isinstance(self.training, DatasetWindow):
            raise TypeError(
                "training must be a DatasetWindow."
            )
        if not isinstance(self.validation, DatasetWindow):
            raise TypeError("validation must be a DatasetWindow.")
        if self.training.requested_range != self.source_window.training_range:
            raise ValueError(
                "training range must match source_window training_range."
            )
        if self.validation.requested_range != self.source_window.validation_range:
            raise ValueError(
                "validation range must match source_window validation_range."
            )


class TrainingValidationSplitEngine(Protocol):
    """Defines injected deterministic split construction without data policies."""

    def split(
        self,
        observations: tuple[Candle, ...],
        window: WalkForwardWindow,
    ) -> WalkForwardDatasetSplit:
        """Return training then validation dataset windows for one source window."""


@dataclass(frozen=True, slots=True)
class StandardTrainingValidationSplitEngine:
    """Delegate exact source ranges to one injected dataset-window builder."""

    dataset_window_builder: DatasetWindowBuilder

    def __post_init__(self) -> None:
        if self.dataset_window_builder is None:
            raise TypeError("dataset_window_builder must not be None.")

    def split(
        self,
        observations: tuple[Candle, ...],
        window: WalkForwardWindow,
    ) -> WalkForwardDatasetSplit:
        """Build training before validation and propagate collaborator failures."""
        if not isinstance(observations, tuple):
            raise TypeError("observations must be a tuple of Candle values.")
        if not isinstance(window, WalkForwardWindow):
            raise TypeError("window must be a WalkForwardWindow.")
        training = self.dataset_window_builder.build(
            observations,
            window.training_range,
        )
        validation = self.dataset_window_builder.build(
            observations,
            window.validation_range,
        )
        return WalkForwardDatasetSplit(window, training, validation)
