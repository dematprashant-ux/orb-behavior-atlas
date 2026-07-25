"""Immutable candidate-evaluation result contracts for future optimizers."""

from dataclasses import dataclass

from src.engines.backtesting.models import BacktestRun
from src.engines.strategy.parameters import CandidateParameterSet

__all__ = ["CandidateEvaluation"]


@dataclass(frozen=True, slots=True)
class CandidateEvaluation:
    """Retain one candidate and its existing immutable backtest outcome.

    The model deliberately references ``BacktestRun`` rather than copying its
    execution results or introducing strategy-performance fields. Future
    optimizers may consume this typed hand-off without imposing ranking or
    scoring semantics at the evaluation-contract boundary.
    """

    candidate: CandidateParameterSet
    outcome: BacktestRun

    def __post_init__(self) -> None:
        """Require the immutable values intrinsic to one evaluation result."""
        if not isinstance(self.candidate, CandidateParameterSet):
            raise TypeError("candidate must be a CandidateParameterSet.")
        if not isinstance(self.outcome, BacktestRun):
            raise TypeError("outcome must be a BacktestRun.")
