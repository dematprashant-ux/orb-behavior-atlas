"""Deterministic Cartesian-product candidate generation for parameter spaces."""

from dataclasses import dataclass
from itertools import product

from src.engines.strategy.parameters import CandidateParameterSet, ParameterSpace

__all__ = ["GridCandidateGenerator"]


@dataclass(frozen=True, slots=True)
class GridCandidateGenerator:
    """Enumerate one finite parameter space in declared product order."""

    def generate(
        self,
        parameter_space: ParameterSpace,
    ) -> tuple[CandidateParameterSet, ...]:
        """Return tuple-backed candidates without evaluation or side effects.

        Values vary in standard Cartesian-product order: the final declared
        parameter changes fastest. An empty parameter space has one explicit
        empty assignment, the mathematical identity of a Cartesian product.
        """
        if not isinstance(parameter_space, ParameterSpace):
            raise TypeError("parameter_space must be a ParameterSpace.")
        names = tuple(parameter.name for parameter in parameter_space.parameters)
        value_spaces = tuple(
            parameter.values for parameter in parameter_space.parameters
        )
        return tuple(
            CandidateParameterSet(tuple(zip(names, values)))
            for values in product(*value_spaces)
        )
