"""Pure Strategy Engine protocol boundary without strategy implementations."""

from typing import Protocol

from src.engines.strategy.models import StrategyContext, StrategyDecision
from src.engines.strategy.parameters import CandidateParameterSet, ParameterSpace

__all__ = ["CandidateGenerator", "Strategy"]


class Strategy(Protocol):
    """Defines the pure evaluation contract for a future strategy implementation."""

    def evaluate(self, context: StrategyContext) -> StrategyDecision:
        """Evaluate an existing context without performing execution or I/O."""


class CandidateGenerator(Protocol):
    """Define deterministic finite candidate enumeration without evaluation."""

    def generate(
        self,
        parameter_space: ParameterSpace,
    ) -> tuple[CandidateParameterSet, ...]:
        """Return ordered immutable candidates from one explicit parameter space."""
