"""Immutable deterministic eligibility constraints for optimization candidates."""

from dataclasses import dataclass
from typing import Protocol

from src.engines.strategy.parameters import CandidateParameterSet

__all__ = ["OptimizationConstraint", "OptimizationConstraints"]


class OptimizationConstraint(Protocol):
    """Determine whether one candidate is eligible for evaluation."""

    def is_eligible(self, candidate: CandidateParameterSet) -> bool:
        """Return deterministic candidate eligibility without evaluation or scoring."""


@dataclass(frozen=True, slots=True)
class OptimizationConstraints:
    """Apply ordered injected eligibility constraints with logical AND semantics."""

    constraints: tuple[OptimizationConstraint, ...] = ()

    def __post_init__(self) -> None:
        """Require immutable explicit constraint storage without invoking it."""
        if not isinstance(self.constraints, tuple):
            raise TypeError("constraints must be a tuple of OptimizationConstraint values.")
        if any(constraint is None for constraint in self.constraints):
            raise TypeError("constraints must not contain None.")

    def is_eligible(self, candidate: CandidateParameterSet) -> bool:
        """Return whether every injected constraint accepts the exact candidate."""
        if not isinstance(candidate, CandidateParameterSet):
            raise TypeError("candidate must be a CandidateParameterSet.")
        return all(constraint.is_eligible(candidate) for constraint in self.constraints)
