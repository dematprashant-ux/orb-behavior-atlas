"""Typed execution boundaries for future walk-forward training and validation."""

from dataclasses import dataclass
from typing import Protocol

from src.engines.backtesting.walk_forward.dataset import DatasetWindow

__all__ = [
    "WalkForwardSelection",
    "WalkForwardTrainer",
    "WalkForwardValidationExecutor",
    "WalkForwardValidationResult",
]


@dataclass(frozen=True, slots=True)
class WalkForwardSelection:
    """Record the explicit opaque identifier selected by a trainer.

    The identifier is intentionally the complete selection payload for this
    contract milestone. It creates a typed hand-off without assuming an
    optimizer, parameter representation, or strategy implementation.
    """

    selection_id: str

    def __post_init__(self) -> None:
        """Require a non-empty deterministic selection identifier."""
        if not isinstance(self.selection_id, str):
            raise TypeError("selection_id must be a str.")
        if not self.selection_id:
            raise ValueError("selection_id must not be empty.")


@dataclass(frozen=True, slots=True)
class WalkForwardValidationResult:
    """Record the selection and canonical dataset window it was validated on.

    This structural result deliberately contains no backtest, optimization, or
    analytics values. Later milestones may introduce domain-specific results
    without changing the trainer and validation-executor boundaries.
    """

    selection: WalkForwardSelection
    validation_window: DatasetWindow

    def __post_init__(self) -> None:
        """Require the typed values intrinsic to one validation result."""
        if not isinstance(self.selection, WalkForwardSelection):
            raise TypeError("selection must be a WalkForwardSelection.")
        if not isinstance(self.validation_window, DatasetWindow):
            raise TypeError("validation_window must be a DatasetWindow.")


class WalkForwardTrainer(Protocol):
    """Define injected training without optimization or dataset construction."""

    def train(self, training_window: DatasetWindow) -> WalkForwardSelection:
        """Return one explicit selection for an existing training window."""


class WalkForwardValidationExecutor(Protocol):
    """Define injected validation without backtest orchestration or analytics."""

    def validate(
        self,
        selection: WalkForwardSelection,
        validation_window: DatasetWindow,
    ) -> WalkForwardValidationResult:
        """Return a typed result for an existing selection and validation window."""
