"""Immutable description of one deterministic optimization experiment."""

from dataclasses import dataclass

from src.engines.backtesting.budget import OptimizationBudget
from src.engines.backtesting.configuration import OptimizationConfiguration
from src.engines.backtesting.constraints import OptimizationConstraints
from src.engines.strategy.parameters import ParameterSpace

__all__ = ["OptimizationSpecification"]


@dataclass(frozen=True, slots=True)
class OptimizationSpecification:
    """Retain what to optimize without owning execution collaborators or results."""

    parameter_space: ParameterSpace
    configuration: OptimizationConfiguration
    budget: OptimizationBudget
    constraints: OptimizationConstraints = OptimizationConstraints()

    def __post_init__(self) -> None:
        """Require existing immutable parameter and policy descriptions."""
        if not isinstance(self.parameter_space, ParameterSpace):
            raise TypeError("parameter_space must be a ParameterSpace.")
        if not isinstance(self.configuration, OptimizationConfiguration):
            raise TypeError("configuration must be an OptimizationConfiguration.")
        if not isinstance(self.budget, OptimizationBudget):
            raise TypeError("budget must be an OptimizationBudget.")
        if not isinstance(self.constraints, OptimizationConstraints):
            raise TypeError("constraints must be an OptimizationConstraints.")
