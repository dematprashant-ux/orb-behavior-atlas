"""Contract tests for deterministic constraint diagnostic descriptions."""

from unittest import TestCase

from src.engines.backtesting import (
    AllOfConstraint,
    AnyOfConstraint,
    ConstraintDiagnostic,
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
        self.assertIsNone(AnyOfConstraint((_Atomic(True), failing)).diagnostic(candidate))
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

    def __init__(self, eligible: bool, identifier: str = "atomic", reason: str = "rejected") -> None:
        self.eligible = eligible
        self.identifier = identifier
        self.reason = reason

    def is_eligible(self, candidate: CandidateParameterSet) -> bool:
        """Return the configured eligibility without mutating its candidate."""
        del candidate
        return self.eligible

    def diagnostic(self, candidate: CandidateParameterSet) -> ConstraintDiagnostic | None:
        """Return a diagnostic only for the configured rejected state."""
        del candidate
        if self.eligible:
            return None
        return ConstraintDiagnostic(self.identifier, self.reason)
