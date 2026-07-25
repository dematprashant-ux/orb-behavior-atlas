"""Immutable deterministic eligibility constraints for optimization candidates."""

from dataclasses import dataclass
from typing import Protocol

from src.engines.strategy.parameters import CandidateParameterSet

__all__ = [
    "AllOfConstraint",
    "AnyOfConstraint",
    "ConstraintDiagnostic",
    "ConstraintEvaluationResult",
    "NotConstraint",
    "OptimizationConstraint",
    "OptimizationConstraints",
]


@dataclass(frozen=True, slots=True)
class ConstraintDiagnostic:
    """Describe one deterministic constraint rejection without execution state."""

    constraint_identifier: str
    rejection_identifier: str

    def __post_init__(self) -> None:
        """Require stable non-blank diagnostic identifiers."""
        for value, name in (
            (self.constraint_identifier, "constraint_identifier"),
            (self.rejection_identifier, "rejection_identifier"),
        ):
            if not isinstance(value, str):
                raise TypeError(f"{name} must be a str.")
            if not value.strip():
                raise ValueError(f"{name} must not be blank.")


@dataclass(frozen=True, slots=True)
class ConstraintEvaluationResult:
    """Retain one authoritative deterministic constraint evaluation outcome."""

    eligible: bool
    diagnostic: ConstraintDiagnostic | None

    def __post_init__(self) -> None:
        """Require exactly one internally consistent eligibility outcome."""
        if not isinstance(self.eligible, bool):
            raise TypeError("eligible must be a bool.")
        if self.eligible and self.diagnostic is not None:
            raise ValueError("eligible results must not have a diagnostic.")
        if not self.eligible and not isinstance(self.diagnostic, ConstraintDiagnostic):
            raise TypeError("rejected results must have a ConstraintDiagnostic.")


class OptimizationConstraint(Protocol):
    """Produce one deterministic eligibility and diagnostic result per candidate."""

    def evaluate(self, candidate: CandidateParameterSet) -> ConstraintEvaluationResult:
        """Return the authoritative immutable result without execution or scoring."""


@dataclass(frozen=True, slots=True)
class AllOfConstraint:
    """Accept a candidate only when every ordered child accepts it."""

    constraints: tuple[OptimizationConstraint, ...] = ()

    def __post_init__(self) -> None:
        """Require immutable non-null child constraints without invoking them."""
        _validate_constraints(self.constraints)

    def is_eligible(self, candidate: CandidateParameterSet) -> bool:
        """Evaluate children in order and short-circuit on first failure."""
        return self.evaluate(candidate).eligible

    def diagnostic(
        self, candidate: CandidateParameterSet
    ) -> ConstraintDiagnostic | None:
        """Return the first failing child diagnostic in deterministic order."""
        return self.evaluate(candidate).diagnostic

    def evaluate(self, candidate: CandidateParameterSet) -> ConstraintEvaluationResult:
        """Return the first failing child result in deterministic order."""
        _validate_candidate(candidate)
        for constraint in self.constraints:
            result = constraint.evaluate(candidate)
            if not result.eligible:
                return result
        return ConstraintEvaluationResult(True, None)


@dataclass(frozen=True, slots=True)
class AnyOfConstraint:
    """Accept a candidate when any ordered child accepts it."""

    constraints: tuple[OptimizationConstraint, ...] = ()

    def __post_init__(self) -> None:
        """Require immutable non-null child constraints without invoking them."""
        _validate_constraints(self.constraints)

    def is_eligible(self, candidate: CandidateParameterSet) -> bool:
        """Evaluate children in order and short-circuit on first success."""
        return self.evaluate(candidate).eligible

    def diagnostic(
        self, candidate: CandidateParameterSet
    ) -> ConstraintDiagnostic | None:
        """Describe all-child rejection only after deterministic child evaluation."""
        return self.evaluate(candidate).diagnostic

    def evaluate(self, candidate: CandidateParameterSet) -> ConstraintEvaluationResult:
        """Return success early or the deterministic all-child rejection result."""
        _validate_candidate(candidate)
        for constraint in self.constraints:
            result = constraint.evaluate(candidate)
            if result.eligible:
                return result
        return ConstraintEvaluationResult(
            False,
            ConstraintDiagnostic("any_of_constraint", "all_children_rejected"),
        )


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
        return self.evaluate(candidate).eligible

    def diagnostic(
        self, candidate: CandidateParameterSet
    ) -> ConstraintDiagnostic | None:
        """Describe rejection when the wrapped constraint accepts the candidate."""
        return self.evaluate(candidate).diagnostic

    def evaluate(self, candidate: CandidateParameterSet) -> ConstraintEvaluationResult:
        """Return the logically negated child outcome using one child evaluation."""
        _validate_candidate(candidate)
        result = self.constraint.evaluate(candidate)
        if not result.eligible:
            return ConstraintEvaluationResult(True, None)
        return ConstraintEvaluationResult(
            False,
            ConstraintDiagnostic("not_constraint", "wrapped_constraint_accepted"),
        )


@dataclass(frozen=True, slots=True)
class OptimizationConstraints:
    """Apply ordered injected eligibility constraints with logical AND semantics."""

    constraints: tuple[OptimizationConstraint, ...] = ()

    def __post_init__(self) -> None:
        """Require immutable explicit constraint storage without invoking it."""
        _validate_constraints(self.constraints)

    def is_eligible(self, candidate: CandidateParameterSet) -> bool:
        """Return whether every injected constraint accepts the exact candidate."""
        return self.evaluate(candidate).eligible

    def diagnostic(
        self, candidate: CandidateParameterSet
    ) -> ConstraintDiagnostic | None:
        """Return the first top-level failing diagnostic in declared order."""
        return self.evaluate(candidate).diagnostic

    def evaluate(self, candidate: CandidateParameterSet) -> ConstraintEvaluationResult:
        """Return the ordered logical-AND result without a duplicate traversal."""
        return AllOfConstraint(self.constraints).evaluate(candidate)


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
