"""Immutable policy configuration for deterministic optimization orchestration."""

from dataclasses import dataclass

from src.engines.backtesting.objectives import ObjectiveDirection
from src.engines.backtesting.selection import SelectionPolicy

__all__ = ["OptimizationConfiguration"]


@dataclass(frozen=True, slots=True)
class OptimizationConfiguration:
    """Retain the explicit direction and selection policy for one pipeline.

    Execution collaborators remain outside this value object so configuration
    describes policy choices without owning execution state or behavior.
    """

    direction: ObjectiveDirection
    selection_policy: SelectionPolicy

    def __post_init__(self) -> None:
        """Require an explicit direction and an injected selection policy."""
        if not isinstance(self.direction, ObjectiveDirection):
            raise TypeError("direction must be an ObjectiveDirection.")
        if self.selection_policy is None:
            raise TypeError("selection_policy must not be None.")
