"""Immutable deterministic evaluation limits for optimization execution."""

from dataclasses import dataclass

__all__ = ["OptimizationBudget"]


@dataclass(frozen=True, slots=True)
class OptimizationBudget:
    """Limit how many candidates one optimization strategy may evaluate."""

    maximum_evaluations: int

    def __post_init__(self) -> None:
        """Require one explicit non-negative integer evaluation limit."""
        if isinstance(self.maximum_evaluations, bool) or not isinstance(
            self.maximum_evaluations,
            int,
        ):
            raise TypeError("maximum_evaluations must be an int.")
        if self.maximum_evaluations < 0:
            raise ValueError("maximum_evaluations must not be negative.")
