"""Optimization search-strategy contracts without scoring or orchestration."""

from dataclasses import dataclass, field
from typing import Protocol

from src.engines.backtesting.grid_search import GridSearchRun, GridSearchRunner
from src.engines.backtesting.progress import OptimizationProgress
from src.engines.backtesting.search import OptimizationSearchRun
from src.engines.backtesting.specification import OptimizationSpecification
from src.engines.backtesting.strategy_metadata import OptimizationStrategyMetadata
from src.engines.strategy.indexing import CartesianParameterSpaceIndexer

__all__ = ["GridOptimizationStrategy", "OptimizationStrategy"]


class OptimizationStrategy(Protocol):
    """Produce source-owned candidate evaluations for one optimization specification."""

    metadata: OptimizationStrategyMetadata

    def execute(
        self,
        specification: OptimizationSpecification,
    ) -> OptimizationSearchRun:
        """Return ordered candidate evaluations without scoring or selection."""


@dataclass(frozen=True, slots=True)
class GridOptimizationStrategy:
    """Adapt one injected grid-search runner to the optimization strategy contract."""

    grid_search_runner: GridSearchRunner
    metadata: OptimizationStrategyMetadata = field(
        default=OptimizationStrategyMetadata("grid"),
        init=False,
    )

    def __post_init__(self) -> None:
        """Require one explicit grid-search execution collaborator."""
        if self.grid_search_runner is None:
            raise TypeError("grid_search_runner must not be None.")
        if not isinstance(self.metadata, OptimizationStrategyMetadata):
            raise TypeError("metadata must be an OptimizationStrategyMetadata.")

    def execute(
        self,
        specification: OptimizationSpecification,
    ) -> OptimizationSearchRun:
        """Delegate once and adapt its exact ordered evaluations to a generic run."""
        if not isinstance(specification, OptimizationSpecification):
            raise TypeError("specification must be an OptimizationSpecification.")
        grid_search_run = self.grid_search_runner.run(
            specification.parameter_space,
            specification.budget,
        )
        if not isinstance(grid_search_run, GridSearchRun):
            raise TypeError("grid_search_runner.run must return a GridSearchRun.")
        if grid_search_run.parameter_space is not specification.parameter_space:
            raise ValueError("grid_search_run must retain the source parameter_space.")
        progress = OptimizationProgress(
            len(grid_search_run.evaluations),
            CartesianParameterSpaceIndexer().cardinality(specification.parameter_space),
        )
        return OptimizationSearchRun(
            self.metadata,
            grid_search_run.evaluations,
            progress,
        )
