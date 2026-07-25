"""Contract tests for finite deterministic parameter-space indexing."""

from enum import Enum
from unittest import TestCase

from src.engines.strategy import (
    CandidateParameterSet,
    CartesianParameterSpaceIndexer,
    DiscreteParameter,
    GridCandidateGenerator,
    ParameterSpace,
    ParameterSpaceIndexer,
)


class _Mode(Enum):
    """Represent an identity-preserving parameter value for contract coverage."""

    FIRST = "first"
    SECOND = "second"


class ParameterSpaceIndexerTests(TestCase):
    """Verify indexed access matches the established canonical grid order."""

    def test_protocol_and_public_exports_are_intentional(self) -> None:
        indexer: ParameterSpaceIndexer = CartesianParameterSpaceIndexer()
        from src.engines.strategy import (
            CartesianParameterSpaceIndexer as PackageIndexer,
        )
        from src.engines.strategy import ParameterSpaceIndexer as PackageProtocol

        self.assertIsInstance(indexer, CartesianParameterSpaceIndexer)
        self.assertIs(PackageIndexer, CartesianParameterSpaceIndexer)
        self.assertIs(PackageProtocol, ParameterSpaceIndexer)

    def test_cardinality_follows_cartesian_product_semantics(self) -> None:
        indexer = CartesianParameterSpaceIndexer()

        self.assertEqual(indexer.cardinality(ParameterSpace(())), 1)
        self.assertEqual(
            indexer.cardinality(
                ParameterSpace((DiscreteParameter("orb_minutes", (15,)),))
            ),
            1,
        )
        self.assertEqual(indexer.cardinality(_parameter_space()), 12)

    def test_candidate_at_matches_grid_generation_in_exact_order(self) -> None:
        parameter_space = _parameter_space()
        indexer = CartesianParameterSpaceIndexer()
        generated = GridCandidateGenerator().generate(parameter_space)
        indexed = tuple(
            indexer.candidate_at(parameter_space, index)
            for index in range(indexer.cardinality(parameter_space))
        )

        self.assertEqual(indexed, generated)
        self.assertEqual(indexed[0].assignments, generated[0].assignments)
        self.assertEqual(indexed[-1].assignments, generated[-1].assignments)

    def test_candidate_at_preserves_declared_values_and_empty_space(self) -> None:
        mode = DiscreteParameter("mode", (_Mode.FIRST, _Mode.SECOND))
        parameter_space = ParameterSpace((mode,))
        indexer = CartesianParameterSpaceIndexer()

        candidate = indexer.candidate_at(parameter_space, 1)

        self.assertIs(candidate.assignments[0][1], mode.values[1])
        self.assertEqual(
            indexer.candidate_at(ParameterSpace(()), 0),
            CandidateParameterSet(()),
        )

    def test_candidate_at_rejects_invalid_indices_without_wraparound(self) -> None:
        indexer = CartesianParameterSpaceIndexer()
        parameter_space = _parameter_space()

        for index in (-1, indexer.cardinality(parameter_space), 13):
            with self.subTest(index=index):
                with self.assertRaisesRegex(ValueError, "index"):
                    indexer.candidate_at(parameter_space, index)
        for index in (True, 1.0, "1"):
            with self.subTest(index=index):
                with self.assertRaisesRegex(TypeError, "index"):
                    indexer.candidate_at(
                        parameter_space,
                        index,
                    )  # type: ignore[arg-type]

    def test_large_space_indexing_uses_exact_integer_cardinality(self) -> None:
        parameter_space = ParameterSpace(
            tuple(
                DiscreteParameter(f"parameter_{index}", tuple(range(10)))
                for index in range(10)
            )
        )
        indexer = CartesianParameterSpaceIndexer()

        self.assertEqual(indexer.cardinality(parameter_space), 10**10)
        self.assertEqual(
            indexer.candidate_at(parameter_space, 10**10 - 1).assignments,
            tuple((f"parameter_{index}", 9) for index in range(10)),
        )


def _parameter_space() -> ParameterSpace:
    """Return a non-uniform declared space for ordering coverage."""
    return ParameterSpace(
        (
            DiscreteParameter("orb_minutes", (5, 15)),
            DiscreteParameter("target_multiple", (1.0, 2.0, 3.0)),
            DiscreteParameter("enabled", (False, True)),
        )
    )
