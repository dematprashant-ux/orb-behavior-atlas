"""Immutable deterministic eligibility constraints for optimization candidates."""

from dataclasses import dataclass
from typing import Protocol

from src.engines.strategy.parameters import CandidateParameterSet

__all__ = [
    "AllOfConstraint",
    "AnyOfConstraint",
    "NotConstraint",
    "OptimizationConstraint",
    "OptimizationConstraints",
]


class OptimizationConstraint(Protocol):
    """Determine whether one candidate is eligible for evaluation."""

    def is_eligible(self, candidate: CandidateParameterSet) -> bool:
        """Return deterministic candidate eligibility without evaluation or scoring."""


@dataclass(frozen=True, slots=True)
class AllOfConstraint:
    """Accept a candidate only when every ordered child accepts it."""

    constraints: tuple[OptimizationConstraint, ...] = ()

    def __post_init__(self) -> None:
        """Require immutable non-null child constraints without invoking them."""
        _validate_constraints(self.constraints)

    def is_eligible(self, candidate: CandidateParameterSet) -> bool:
        """Evaluate children in order and short-circuit on first failure."""
        _validate_candidate(candidate)
        return all(constraint.is_eligible(candidate) for constraint in self.constraints)


@dataclass(frozen=True, slots=True)
class AnyOfConstraint:
    """Accept a candidate when any ordered child accepts it."""

    constraints: tuple[OptimizationConstraint, ...] = ()

    def __post_init__(self) -> None:
        """Require immutable non-null child constraints without invoking them."""
        _validate_constraints(self.constraints)

    def is_eligible(self, candidate: CandidateParameterSet) -> bool:
        """Evaluate children in order and short-circuit on first success."""
        _validate_candidate(candidate)
        return any(constraint.is_eligible(candidate) for constraint in self.constraints)


@dataclass(frozen=True, slots=True)
class NotConstraint:
    """Negate one exact child constraint without changing its evaluation order."""

    constraint: OptimizationConstraint

    def __post_init__(self) -> None:
        """Require one explicit child constraint without invoking it."""
        if self.constraint is None:
            raise TypeError("constraint must not be None.")

    def is_eligible(self, candidate: CandidateParameterSet) -> bool:
        """Return the logical negation of the wrapped constraint result."""
        _validate_candidate(candidate)
        return not self.constraint.is_eligible(candidate)


@dataclass(frozen=True, slots=True)
class OptimizationConstraints:
    """Apply ordered injected eligibility constraints with logical AND semantics."""

    constraints: tuple[OptimizationConstraint, ...] = ()

    def __post_init__(self) -> None:
        """Require immutable explicit constraint storage without invoking it."""
        _validate_constraints(self.constraints)

    def is_eligible(self, candidate: CandidateParameterSet) -> bool:
        """Return whether every injected constraint accepts the exact candidate."""
        _validate_candidate(candidate)
        return all(constraint.is_eligible(candidate) for constraint in self.constraints)


def _validate_constraints(constraints: tuple[OptimizationConstraint, ...]) -> None:
    """Require immutable ordered non-null child constraint storage."""
    if not isinstance(constraints, tuple):
        raise TypeError("constraints must be a tuple of OptimizationConstraint values.")
    if any(constraint is None for constraint in constraints):
        raise TypeError("constraints must not contain None.")


def _validate_candidate(candidate: CandidateParameterSet) -> None:
    """Require the existing immutable candidate representation at this boundary."""
    if not isinstance(candidate, CandidateParameterSet):
        raise TypeError("candidate must be a CandidateParameterSet.")
