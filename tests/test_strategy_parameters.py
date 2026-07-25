"""Contract tests for immutable finite Strategy Engine parameter domains."""

from dataclasses import FrozenInstanceError, is_dataclass
from enum import Enum
from math import inf, nan
from unittest import TestCase

from src.engines.strategy import (
    CandidateParameterSet,
    DiscreteParameter,
    ParameterDefinition,
    ParameterSpace,
)


class StrategyParameterDomainTests(TestCase):
    """Verify typed finite candidate parameter descriptions without search logic."""

    def test_discrete_parameter_is_immutable_ordered_and_deterministic(self) -> None:
        parameter = DiscreteParameter("orb_minutes", (5, 15, 30))

        self.assertTrue(is_dataclass(parameter))
        self.assertFalse(hasattr(parameter, "__dict__"))
        self.assertEqual(parameter.values, (5, 15, 30))
        self.assertEqual(parameter, DiscreteParameter("orb_minutes", (5, 15, 30)))
        self.assertEqual(repr(parameter), repr(DiscreteParameter("orb_minutes", (5, 15, 30))))
        with self.assertRaises(FrozenInstanceError):
            parameter.name = "changed"  # type: ignore[misc]

    def test_definition_rejects_blank_empty_duplicate_mixed_and_unsafe_values(self) -> None:
        with self.assertRaisesRegex(ValueError, "blank"):
            ParameterDefinition("   ", (1,))
        with self.assertRaisesRegex(ValueError, "empty"):
            ParameterDefinition("orb_minutes", ())
        with self.assertRaisesRegex(ValueError, "duplicates"):
            ParameterDefinition("orb_minutes", (5, 5))
        with self.assertRaisesRegex(TypeError, "compatible"):
            ParameterDefinition("orb_minutes", (5, 5.0))
        with self.assertRaisesRegex(TypeError, "parameter values"):
            ParameterDefinition("orb_minutes", (object(),))
        with self.assertRaisesRegex(ValueError, "finite"):
            ParameterDefinition("multiple", (1.0, inf))
        with self.assertRaisesRegex(ValueError, "finite"):
            ParameterDefinition("multiple", (1.0, nan))

    def test_bool_int_and_enum_values_are_explicitly_distinguished(self) -> None:
        enabled = DiscreteParameter("enabled", (False, True))
        direction = DiscreteParameter("direction", (_Direction.UP, _Direction.DOWN))

        self.assertEqual(enabled.values, (False, True))
        self.assertEqual(direction.values, (_Direction.UP, _Direction.DOWN))
        with self.assertRaisesRegex(TypeError, "compatible"):
            ParameterDefinition("invalid", (False, 1))
        with self.assertRaisesRegex(TypeError, "compatible"):
            ParameterDefinition("invalid", (_Direction.UP, _OtherDirection.UP))

    def test_candidate_parameter_set_is_ordered_immutable_mapping_like_value(self) -> None:
        candidate = CandidateParameterSet(
            (("orb_minutes", 15), ("enabled", True), ("label", "baseline"))
        )

        self.assertEqual(tuple(candidate), ("orb_minutes", "enabled", "label"))
        self.assertEqual(tuple(candidate.items()), candidate.assignments)
        self.assertEqual(candidate["enabled"], True)
        self.assertEqual(candidate, CandidateParameterSet(candidate.assignments))
        self.assertEqual(repr(candidate), repr(CandidateParameterSet(candidate.assignments)))
        with self.assertRaises(FrozenInstanceError):
            candidate.assignments = ()  # type: ignore[misc]
        with self.assertRaisesRegex(ValueError, "duplicate"):
            CandidateParameterSet((("orb_minutes", 5), ("orb_minutes", 15)))

    def test_parameter_space_retains_only_ordered_discrete_definitions(self) -> None:
        space = ParameterSpace(
            (
                DiscreteParameter("orb_minutes", (5, 15)),
                DiscreteParameter("enabled", (False, True)),
                DiscreteParameter("direction", (_Direction.UP, _Direction.DOWN)),
            )
        )

        self.assertEqual(tuple(parameter.name for parameter in space.parameters), (
            "orb_minutes",
            "enabled",
            "direction",
        ))
        self.assertFalse(hasattr(space, "candidate"))

    def test_parameter_space_rejects_duplicate_names_and_non_tuple_inputs(self) -> None:
        parameter = DiscreteParameter("orb_minutes", (5, 15))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            ParameterSpace((parameter, parameter))
        with self.assertRaisesRegex(TypeError, "tuple"):
            ParameterSpace([parameter])

    def test_public_strategy_exports_reference_parameter_domain_types(self) -> None:
        from src.engines.strategy import ParameterValue

        self.assertEqual(ParameterValue, bool | int | float | str | Enum)


class _Direction(str, Enum):
    """Representative stable enum-backed parameter values."""

    UP = "UP"
    DOWN = "DOWN"


class _OtherDirection(str, Enum):
    """Different enum type used to verify homogeneous definition enforcement."""

    UP = "UP"
