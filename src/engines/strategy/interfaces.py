"""Pure Strategy Engine protocol boundary without strategy implementations."""

from typing import Protocol

from src.engines.strategy.models import StrategyContext, StrategyDecision

__all__ = ["Strategy"]


class Strategy(Protocol):
    """Defines the pure evaluation contract for a future strategy implementation."""

    def evaluate(self, context: StrategyContext) -> StrategyDecision:
        """Evaluate an existing context without performing execution or I/O."""
