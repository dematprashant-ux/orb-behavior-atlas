"""Deterministic candidate sampling contracts without candidate evaluation."""

from dataclasses import dataclass
from math import prod
from random import Random
from typing import Protocol

from src.engines.strategy.parameters import (
    CandidateParameterSet,
    ParameterSpace,
    ParameterValue,
)

__all__ = [
    "DeterministicRandomCandidateSampler",
    "RandomCandidateSampler",
    "RandomOptimizationConfiguration",
]


@dataclass(frozen=True, slots=True)
class RandomOptimizationConfiguration:
    """Retain the explicit seed and finite sample limit for random sampling."""

    seed: int
    maximum_samples: int

    def __post_init__(self) -> None:
        """Require reproducible integer configuration without hidden defaults."""
        if isinstance(self.seed, bool) or not isinstance(self.seed, int):
            raise TypeError("seed must be an int.")
        if isinstance(self.maximum_samples, bool) or not isinstance(
            self.maximum_samples,
            int,
        ):
            raise TypeError("maximum_samples must be an int.")
        if self.maximum_samples < 0:
            raise ValueError("maximum_samples must not be negative.")


class RandomCandidateSampler(Protocol):
    """Produce ordered unique finite candidates without evaluating them."""

    def sample(
        self,
        parameter_space: ParameterSpace,
        configuration: RandomOptimizationConfiguration,
    ) -> tuple[CandidateParameterSet, ...]:
        """Return seeded candidates without scoring, evaluation, or mutation."""


@dataclass(frozen=True, slots=True)
class DeterministicRandomCandidateSampler:
    """Sample finite Cartesian-product positions without full enumeration."""

    def sample(
        self,
        parameter_space: ParameterSpace,
        configuration: RandomOptimizationConfiguration,
    ) -> tuple[CandidateParameterSet, ...]:
        """Return seeded unique candidates in their stable sampled order."""
        if not isinstance(parameter_space, ParameterSpace):
            raise TypeError("parameter_space must be a ParameterSpace.")
        if not isinstance(configuration, RandomOptimizationConfiguration):
            raise TypeError(
                "configuration must be a RandomOptimizationConfiguration."
            )

        total_candidates = prod(
            len(parameter.values) for parameter in parameter_space.parameters
        )
        sample_count = min(configuration.maximum_samples, total_candidates)
        sampled_indices = Random(configuration.seed).sample(
            range(total_candidates),
            sample_count,
        )
        return tuple(
            _candidate_at_index(parameter_space, index)
            for index in sampled_indices
        )


def _candidate_at_index(
    parameter_space: ParameterSpace,
    index: int,
) -> CandidateParameterSet:
    """Map one Cartesian-product index to its declared parameter assignments."""
    assignments: list[tuple[str, ParameterValue]] = []
    remaining = index
    for parameter in reversed(parameter_space.parameters):
        value_index = remaining % len(parameter.values)
        remaining //= len(parameter.values)
        assignments.append((parameter.name, parameter.values[value_index]))
    return CandidateParameterSet(tuple(reversed(assignments)))
