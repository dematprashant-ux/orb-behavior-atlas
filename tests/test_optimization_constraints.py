"""Contract tests for deterministic composable optimization constraints."""

from unittest import TestCase

from src.engines.backtesting import (
    AllOfConstraint,
    AnyOfConstraint,
    NotConstraint,
    OptimizationConstraints,
)
from src.engines.strategy import CandidateParameterSet


class OptimizationConstraintCompositionTests(TestCase):
    """Verify logical composition is ordered, deterministic, and short-circuiting."""

    def test_all_of_short_circuits_on_first_failure(self) -> None:
        events: list[str] = []
        constraint = AllOfConstraint(
            (_Constraint(False, "first", events), _Constraint(True, "second", events))
        )

        self.assertFalse(constraint.is_eligible(_candidate()))
        self.assertEqual(events, ["first"])

    def test_any_of_short_circuits_on_first_success(self) -> None:
        events: list[str] = []
        constraint = AnyOfConstraint(
            (_Constraint(True, "first", events), _Constraint(False, "second", events))
        )

        self.assertTrue(constraint.is_eligible(_candidate()))
        self.assertEqual(events, ["first"])

    def test_not_and_nested_composition_are_deterministic(self) -> None:
        candidate = _candidate()
        constraint = AnyOfConstraint(
            (
                AllOfConstraint((_Constraint(True), _Constraint(False))),
                NotConstraint(
                    AnyOfConstraint((_Constraint(False), _Constraint(False)))
                ),
            )
        )

        self.assertTrue(constraint.is_eligible(candidate))
        self.assertTrue(OptimizationConstraints((constraint,)).is_eligible(candidate))

    def test_empty_compositions_follow_identity_semantics(self) -> None:
        candidate = _candidate()

        self.assertTrue(AllOfConstraint().is_eligible(candidate))
        self.assertFalse(AnyOfConstraint().is_eligible(candidate))
        self.assertTrue(OptimizationConstraints().is_eligible(candidate))

    def test_public_exports_are_intentional(self) -> None:
        from src.engines.backtesting import AllOfConstraint as PackageAllOf
        from src.engines.backtesting import AnyOfConstraint as PackageAnyOf
        from src.engines.backtesting import NotConstraint as PackageNot

        self.assertIs(PackageAllOf, AllOfConstraint)
        self.assertIs(PackageAnyOf, AnyOfConstraint)
        self.assertIs(PackageNot, NotConstraint)


class _Constraint:
    """Test-only deterministic atomic constraint with optional evaluation trace."""

    def __init__(
        self,
        result: bool,
        name: str = "",
        events: list[str] | None = None,
    ) -> None:
        self.result = result
        self.name = name
        self.events = events

    def is_eligible(self, candidate: CandidateParameterSet) -> bool:
        """Record the exact evaluation order without mutating the candidate."""
        del candidate
        if self.events is not None:
            self.events.append(self.name)
        return self.result


def _candidate() -> CandidateParameterSet:
    """Return one existing immutable parameter candidate."""
    return CandidateParameterSet((("orb_minutes", 15),))
