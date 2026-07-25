"""Contract tests for authoritative immutable constraint evaluation results."""

from dataclasses import FrozenInstanceError
from unittest import TestCase

from src.engines.backtesting import (
    AllOfConstraint,
    AnyOfConstraint,
    ConstraintDiagnostic,
    ConstraintEvaluationResult,
    NotConstraint,
)
from src.engines.strategy import CandidateParameterSet


class ConstraintEvaluationResultTests(TestCase):
    """Verify one constraint result retains eligibility and diagnostics together."""

    def test_result_is_immutable_deterministic_and_internally_consistent(self) -> None:
        diagnostic = ConstraintDiagnostic("minimum_orb", "too_short")
        eligible = ConstraintEvaluationResult(True, None)
        rejected = ConstraintEvaluationResult(False, diagnostic)

        self.assertEqual(eligible, ConstraintEvaluationResult(True, None))
        self.assertEqual(
            repr(rejected),
            repr(ConstraintEvaluationResult(False, diagnostic)),
        )
        with self.assertRaises(FrozenInstanceError):
            eligible.eligible = False  # type: ignore[misc]
        with self.assertRaisesRegex(ValueError, "eligible"):
            ConstraintEvaluationResult(True, diagnostic)
        with self.assertRaisesRegex(TypeError, "rejected"):
            ConstraintEvaluationResult(False, None)

    def test_composites_return_one_short_circuited_authoritative_result(self) -> None:
        candidate = CandidateParameterSet((("orb_minutes", 15),))
        events: list[str] = []
        failed = _Atomic(False, "failed", events)
        succeeded = _Atomic(True, "succeeded", events)

        all_result = AllOfConstraint((failed, succeeded)).evaluate(candidate)
        self.assertFalse(all_result.eligible)
        self.assertEqual(events, ["failed"])

        events.clear()
        any_result = AnyOfConstraint((succeeded, failed)).evaluate(candidate)
        self.assertTrue(any_result.eligible)
        self.assertEqual(events, ["succeeded"])

        not_result = NotConstraint(succeeded).evaluate(candidate)
        self.assertFalse(not_result.eligible)
        self.assertEqual(
            not_result.diagnostic,
            ConstraintDiagnostic("not_constraint", "wrapped_constraint_accepted"),
        )

    def test_public_export_is_intentional(self) -> None:
        from src.engines.backtesting import (
            ConstraintEvaluationResult as PackageResult,
        )

        self.assertIs(PackageResult, ConstraintEvaluationResult)


class _Atomic:
    """Test-only atomic constraint exposing one recorded result operation."""

    def __init__(self, eligible: bool, name: str, events: list[str]) -> None:
        self.eligible = eligible
        self.name = name
        self.events = events

    def evaluate(self, candidate: CandidateParameterSet) -> ConstraintEvaluationResult:
        """Record one exact traversal and return a deterministic value result."""
        del candidate
        self.events.append(self.name)
        if self.eligible:
            return ConstraintEvaluationResult(True, None)
        return ConstraintEvaluationResult(
            False,
            ConstraintDiagnostic(self.name, "rejected"),
        )
