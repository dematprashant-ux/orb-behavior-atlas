"""Deterministic finite random-search optimization strategy."""

from dataclasses import dataclass, field
from math import prod
from random import Random

from src.engines.backtesting.grid_search import StandardGridSearchRunner
from src.engines.backtesting.interfaces import CandidateEvaluator
from src.engines.backtesting.search import OptimizationSearchRun
from src.engines.backtesting.specification import OptimizationSpecification
from src.engines.backtesting.strategy_metadata import OptimizationStrategyMetadata
from src.engines.strategy.parameters import (
    CandidateParameterSet,
    ParameterSpace,
    ParameterValue,
)

__all__ = ["RandomOptimizationConfiguration", "RandomOptimizationStrategy"]


@dataclass(frozen=True, slots=True)
class RandomOptimizationConfiguration:
    """Retain the explicit seed and finite sample limit for random search."""

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


@dataclass(frozen=True, slots=True)
class RandomOptimizationStrategy:
    """Sample unique candidates deterministically and reuse standard evaluation."""

    candidate_evaluator: CandidateEvaluator
    configuration: RandomOptimizationConfiguration
    metadata: OptimizationStrategyMetadata = field(
        default=OptimizationStrategyMetadata("random"),
        init=False,
    )

    def __post_init__(self) -> None:
        """Require an evaluator and explicit deterministic sampling configuration."""
        if self.candidate_evaluator is None:
            raise TypeError("candidate_evaluator must not be None.")
        if not isinstance(self.configuration, RandomOptimizationConfiguration):
            raise TypeError("configuration must be a RandomOptimizationConfiguration.")

    def execute(
        self,
        specification: OptimizationSpecification,
    ) -> OptimizationSearchRun:
        """Sample and evaluate candidates without scoring, ranking, or selection."""
        if not isinstance(specification, OptimizationSpecification):
            raise TypeError("specification must be an OptimizationSpecification.")
        grid_search_run = StandardGridSearchRunner(
            _RandomCandidateGenerator(self.configuration),
            self.candidate_evaluator,
        ).run(specification.parameter_space)
        return OptimizationSearchRun(self.metadata, grid_search_run.evaluations)


@dataclass(frozen=True, slots=True)
class _RandomCandidateGenerator:
    """Sample unique finite Cartesian-product positions without full enumeration."""

    configuration: RandomOptimizationConfiguration

    def generate(
        self,
        parameter_space: ParameterSpace,
    ) -> tuple[CandidateParameterSet, ...]:
        """Return deterministic unique candidates in sampled order."""
        if not isinstance(parameter_space, ParameterSpace):
            raise TypeError("parameter_space must be a ParameterSpace.")
        total_candidates = prod(
            len(parameter.values) for parameter in parameter_space.parameters
        )
        sample_count = min(self.configuration.maximum_samples, total_candidates)
        sampled_indices = Random(self.configuration.seed).sample(
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
