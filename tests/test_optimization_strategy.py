"""Contract tests for optimization search strategies without new algorithms."""

from dataclasses import dataclass
from unittest import TestCase

from src.engines.backtesting import (
    GridOptimizationStrategy,
    GridSearchRun,
    ObjectiveDirection,
    ObjectiveRanking,
    ObjectiveSelection,
    OptimizationConfiguration,
    OptimizationBudget,
    OptimizationConstraints,
    OptimizationSearchRun,
    OptimizationSpecification,
    OptimizationStrategy,
    OptimizationStrategyMetadata,
)
from src.engines.strategy import DiscreteParameter, ParameterSpace


class OptimizationStrategyTests(TestCase):
    """Verify strategy delegation without scoring, ranking, or selection logic."""

    def test_grid_strategy_delegates_once_and_adapts_the_grid_result(self) -> None:
        specification = _specification()
        expected = GridSearchRun(specification.parameter_space)
        grid_search_runner = _GridSearchRunner(expected)
        strategy: OptimizationStrategy = GridOptimizationStrategy(grid_search_runner)

        result = strategy.execute(specification)

        self.assertIsInstance(result, OptimizationSearchRun)
        self.assertIs(result.strategy_metadata, strategy.metadata)
        self.assertIs(result.evaluations, expected.evaluations)
        self.assertEqual(
            grid_search_runner.parameter_spaces,
            [specification.parameter_space],
        )
        self.assertEqual(grid_search_runner.budgets, [specification.budget])

    def test_grid_strategy_rejects_intrinsic_misuse(self) -> None:
        with self.assertRaisesRegex(TypeError, "grid_search_runner"):
            GridOptimizationStrategy(None)  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "specification"):
            GridOptimizationStrategy(
                _GridSearchRunner(GridSearchRun(_space()))
            ).execute(None)  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "parameter_space"):
            GridOptimizationStrategy(
                _GridSearchRunner(GridSearchRun(_space()))
            ).execute(_specification())

    def test_public_exports_are_intentional(self) -> None:
        from src.engines.backtesting import GridOptimizationStrategy as PackageGrid
        from src.engines.backtesting import OptimizationStrategy as PackageStrategy

        self.assertIs(PackageGrid, GridOptimizationStrategy)
        self.assertIs(PackageStrategy, OptimizationStrategy)


class _GridSearchRunner:
    """Test double that retains exact parameter-space input references."""

    def __init__(self, result: GridSearchRun) -> None:
        self.result = result
        self.parameter_spaces: list[ParameterSpace] = []
        self.budgets: list[OptimizationBudget] = []
        self.constraints: list[OptimizationConstraints] = []

    def run(
        self,
        parameter_space: ParameterSpace,
        budget: OptimizationBudget,
        constraints: OptimizationConstraints,
    ) -> GridSearchRun:
        """Record the exact supplied space and return the configured result."""
        self.parameter_spaces.append(parameter_space)
        self.budgets.append(budget)
        self.constraints.append(constraints)
        return self.result


@dataclass(frozen=True, slots=True)
class _SelectionPolicy:
    """Minimal immutable structural selection policy for one specification."""

    def select(self, ranking: ObjectiveRanking) -> ObjectiveSelection:
        """Return an empty selection for the exact supplied ranking."""
        return ObjectiveSelection(ranking)


def _space() -> ParameterSpace:
    """Return one finite immutable space for strategy-adapter contract tests."""
    return ParameterSpace((DiscreteParameter("orb_minutes", (5, 15)),))


def _specification() -> OptimizationSpecification:
    """Create one immutable strategy input without execution collaborators."""
    return OptimizationSpecification(
        _space(),
        OptimizationConfiguration(ObjectiveDirection.MAXIMIZE, _SelectionPolicy()),
        OptimizationBudget(2),
    )
