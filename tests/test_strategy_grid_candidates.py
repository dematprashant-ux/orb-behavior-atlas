"""Contract tests for deterministic finite grid candidate generation."""

from dataclasses import FrozenInstanceError, is_dataclass
from unittest import TestCase

from src.engines.strategy import (
    CandidateGenerator,
    DiscreteParameter,
    GridCandidateGenerator,
    ParameterSpace,
)


class GridCandidateGeneratorTests(TestCase):
    """Verify Cartesian enumeration without evaluation or optimizer behavior."""

    def test_generate_preserves_parameter_and_value_product_order(self) -> None:
        space = ParameterSpace(
            (
                DiscreteParameter("orb_minutes", (5, 15)),
                DiscreteParameter("target_multiple", (1.0, 2.0)),
                DiscreteParameter("enabled", (False, True)),
            )
        )
        generator: CandidateGenerator = GridCandidateGenerator()

        candidates = generator.generate(space)

        self.assertEqual(
            tuple(candidate.assignments for candidate in candidates),
            (
                (("orb_minutes", 5), ("target_multiple", 1.0), ("enabled", False)),
                (("orb_minutes", 5), ("target_multiple", 1.0), ("enabled", True)),
                (("orb_minutes", 5), ("target_multiple", 2.0), ("enabled", False)),
                (("orb_minutes", 5), ("target_multiple", 2.0), ("enabled", True)),
                (("orb_minutes", 15), ("target_multiple", 1.0), ("enabled", False)),
                (("orb_minutes", 15), ("target_multiple", 1.0), ("enabled", True)),
                (("orb_minutes", 15), ("target_multiple", 2.0), ("enabled", False)),
                (("orb_minutes", 15), ("target_multiple", 2.0), ("enabled", True)),
            ),
        )

    def test_empty_space_returns_the_single_empty_product_candidate(self) -> None:
        candidates = GridCandidateGenerator().generate(ParameterSpace(()))

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].assignments, ())

    def test_generation_is_deterministic_immutable_and_non_mutating(self) -> None:
        space = ParameterSpace((DiscreteParameter("orb_minutes", (5, 15)),))
        generator = GridCandidateGenerator()

        first = generator.generate(space)
        second = generator.generate(space)

        self.assertEqual(first, second)
        self.assertEqual(repr(first), repr(second))
        self.assertEqual(
            tuple(candidate.assignments for candidate in first),
            ((("orb_minutes", 5),), (("orb_minutes", 15),)),
        )
        self.assertEqual(space.parameters[0].values, (5, 15))
        self.assertTrue(is_dataclass(generator))
        self.assertFalse(hasattr(generator, "__dict__"))
        with self.assertRaises((FrozenInstanceError, TypeError)):
            generator.unused = None  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            first[0].assignments = ()  # type: ignore[misc]

    def test_generator_rejects_invalid_public_boundary_and_is_exported(self) -> None:
        with self.assertRaisesRegex(TypeError, "parameter_space"):
            GridCandidateGenerator().generate(None)  # type: ignore[arg-type]

        from src.engines.strategy import GridCandidateGenerator as PackageGenerator

        self.assertIs(PackageGenerator, GridCandidateGenerator)
