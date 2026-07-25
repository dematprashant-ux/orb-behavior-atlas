"""Deterministic candidate sampling contracts without candidate evaluation."""

from dataclasses import dataclass
from random import Random
from typing import Protocol

from src.engines.strategy.parameters import (
    CandidateParameterSet,
    ParameterSpace,
)
from src.engines.strategy.indexing import ParameterSpaceIndexer

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

    parameter_space_indexer: ParameterSpaceIndexer

    def __post_init__(self) -> None:
        """Require one explicit finite-space indexing collaborator."""
        if self.parameter_space_indexer is None:
            raise TypeError("parameter_space_indexer must not be None.")

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

        total_candidates = self.parameter_space_indexer.cardinality(parameter_space)
        sample_count = min(configuration.maximum_samples, total_candidates)
        sampled_indices = Random(configuration.seed).sample(
            range(total_candidates),
            sample_count,
        )
        return tuple(
            self.parameter_space_indexer.candidate_at(parameter_space, index)
            for index in sampled_indices
        )
