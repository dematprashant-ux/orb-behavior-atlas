"""Immutable deterministic optimization execution progress information."""

from dataclasses import dataclass

__all__ = ["OptimizationProgress"]


@dataclass(frozen=True, slots=True)
class OptimizationProgress:
    """Describe completed and total finite candidate work without controlling it."""

    evaluated_candidates: int
    total_candidates: int

    def __post_init__(self) -> None:
        """Require consistent non-negative integer work counts."""
        for value, name in (
            (self.evaluated_candidates, "evaluated_candidates"),
            (self.total_candidates, "total_candidates"),
        ):
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an int.")
            if value < 0:
                raise ValueError(f"{name} must not be negative.")
        if self.evaluated_candidates > self.total_candidates:
            raise ValueError("evaluated_candidates must not exceed total_candidates.")

    @property
    def completion_ratio(self) -> float:
        """Return deterministic completed-work ratio without execution effects."""
        if self.total_candidates == 0:
            return 0.0
        return self.evaluated_candidates / self.total_candidates
