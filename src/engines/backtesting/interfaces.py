"""Pure Backtesting Engine protocol boundary without a backtest implementation."""

from typing import Protocol

from src.engines.backtesting.costs import TransactionCostBreakdown
from src.engines.backtesting.evaluation import CandidateEvaluation
from src.engines.backtesting.models import BacktestContext, BacktestRun
from src.engines.strategy.parameters import CandidateParameterSet

__all__ = ["BacktestEngine", "CandidateEvaluator", "TransactionCostModel"]


class BacktestEngine(Protocol):
    """Defines the pure run contract for a future backtest implementation."""

    def run(self, context: BacktestContext) -> BacktestRun:
        """Return a structural run without implying replay or simulation behavior."""


class CandidateEvaluator(Protocol):
    """Define one injected candidate evaluation without optimizer behavior."""

    def evaluate(self, candidate: CandidateParameterSet) -> CandidateEvaluation:
        """Return one typed outcome without ranking, scoring, or mutation."""


class TransactionCostModel(Protocol):
    """Defines a pure cost calculation over explicit completed-trade facts."""

    def calculate(
        self,
        *,
        entry_price: float,
        exit_price: float,
        quantity: int,
    ) -> TransactionCostBreakdown:
        """Return a finite immutable cost breakdown without PnL integration."""
