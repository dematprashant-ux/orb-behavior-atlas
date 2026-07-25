"""Deterministic finite parameter-space indexing without candidate enumeration."""

from dataclasses import dataclass
from math import prod
from typing import Protocol

from src.engines.strategy.parameters import (
    CandidateParameterSet,
    ParameterSpace,
    ParameterValue,
)

__all__ = ["CartesianParameterSpaceIndexer", "ParameterSpaceIndexer"]


class ParameterSpaceIndexer(Protocol):
    """Resolve finite parameter-space candidates by canonical zero-based index."""

    def cardinality(self, parameter_space: ParameterSpace) -> int:
        """Return the exact finite Cartesian-product cardinality."""

    def candidate_at(
        self,
        parameter_space: ParameterSpace,
        index: int,
    ) -> CandidateParameterSet:
        """Return one canonical candidate without enumerating the full space."""


@dataclass(frozen=True, slots=True)
class CartesianParameterSpaceIndexer:
    """Resolve canonical Cartesian-product candidates with mixed-radix indexing."""

    def cardinality(self, parameter_space: ParameterSpace) -> int:
        """Return the product of declared value counts in one parameter pass."""
        if not isinstance(parameter_space, ParameterSpace):
            raise TypeError("parameter_space must be a ParameterSpace.")
        return prod(
            len(parameter.values) for parameter in parameter_space.parameters
        )

    def candidate_at(
        self,
        parameter_space: ParameterSpace,
        index: int,
    ) -> CandidateParameterSet:
        """Resolve one zero-based canonical candidate in mixed-radix order."""
        if not isinstance(parameter_space, ParameterSpace):
            raise TypeError("parameter_space must be a ParameterSpace.")
        if isinstance(index, bool) or not isinstance(index, int):
            raise TypeError("index must be an int.")

        cardinality = self.cardinality(parameter_space)
        if index < 0 or index >= cardinality:
            raise ValueError("index must identify one candidate in parameter_space.")

        assignments: list[tuple[str, ParameterValue]] = []
        remaining = index
        for parameter in reversed(parameter_space.parameters):
            value_index = remaining % len(parameter.values)
            remaining //= len(parameter.values)
            assignments.append((parameter.name, parameter.values[value_index]))
        return CandidateParameterSet(tuple(reversed(assignments)))
