"""Immutable algorithm-neutral candidate-evaluation search results."""

from dataclasses import dataclass

from src.engines.backtesting.evaluation import CandidateEvaluation

__all__ = ["OptimizationSearchRun"]


@dataclass(frozen=True, slots=True)
class OptimizationSearchRun:
    """Retain ordered candidate evaluations without algorithm-specific state."""

    evaluations: tuple[CandidateEvaluation, ...] = ()

    def __post_init__(self) -> None:
        """Require immutable typed evaluations without sorting or filtering them."""
        if not isinstance(self.evaluations, tuple):
            raise TypeError(
                "evaluations must be a tuple of CandidateEvaluation values."
            )
        if any(
            not isinstance(evaluation, CandidateEvaluation)
            for evaluation in self.evaluations
        ):
            raise TypeError("evaluations must contain only CandidateEvaluation values.")
