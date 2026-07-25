"""Contract tests for deterministic constraint diagnostic descriptions."""

from unittest import TestCase

from src.engines.backtesting import (
    AllOfConstraint,
    AnyOfConstraint,
    ConstraintDiagnostic,
    ConstraintEvaluationResult,
    NotConstraint,
)
from src.engines.strategy import CandidateParameterSet


class ConstraintDiagnosticTests(TestCase):
    """Verify diagnostics remain descriptive and preserve composition semantics."""

    def test_atomic_and_composed_diagnostics_are_deterministic(self) -> None:
        candidate = CandidateParameterSet((("orb_minutes", 15),))
        failing = _Atomic(False, "minimum_orb", "too_short")

        self.assertEqual(
            AllOfConstraint((failing,)).diagnostic(candidate),
            ConstraintDiagnostic("minimum_orb", "too_short"),
        )
        self.assertIsNone(
            AnyOfConstraint((_Atomic(True), failing)).diagnostic(candidate)
        )
        self.assertEqual(
            AnyOfConstraint((failing,)).diagnostic(candidate),
            ConstraintDiagnostic("any_of_constraint", "all_children_rejected"),
        )
        self.assertEqual(
            NotConstraint(_Atomic(True)).diagnostic(candidate),
            ConstraintDiagnostic("not_constraint", "wrapped_constraint_accepted"),
        )


class _Atomic:
    """Test-only atomic constraint providing an explicit stable diagnostic."""

    def __init__(
        self,
        eligible: bool,
        identifier: str = "atomic",
        reason: str = "rejected",
    ) -> None:
        self.eligible = eligible
        self.identifier = identifier
        self.reason = reason

    def evaluate(self, candidate: CandidateParameterSet) -> ConstraintEvaluationResult:
        """Return one configured result without mutating its candidate."""
        del candidate
        if self.eligible:
            return ConstraintEvaluationResult(True, None)
        return ConstraintEvaluationResult(
            False,
            ConstraintDiagnostic(self.identifier, self.reason),
        )
