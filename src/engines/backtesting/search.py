"""Immutable algorithm-neutral candidate-evaluation search results."""

from dataclasses import dataclass

from src.engines.backtesting.evaluation import CandidateEvaluation
from src.engines.backtesting.progress import OptimizationProgress
from src.engines.backtesting.strategy_metadata import OptimizationStrategyMetadata

__all__ = ["OptimizationSearchRun"]


@dataclass(frozen=True, slots=True)
class OptimizationSearchRun:
    """Retain ordered candidate evaluations without algorithm-specific state."""

    strategy_metadata: OptimizationStrategyMetadata
    evaluations: tuple[CandidateEvaluation, ...] = ()
    progress: OptimizationProgress | None = None

    def __post_init__(self) -> None:
        """Require immutable typed evaluations without sorting or filtering them."""
        if not isinstance(self.strategy_metadata, OptimizationStrategyMetadata):
            raise TypeError(
                "strategy_metadata must be an OptimizationStrategyMetadata."
            )
        if not isinstance(self.evaluations, tuple):
            raise TypeError(
                "evaluations must be a tuple of CandidateEvaluation values."
            )
        if any(
            not isinstance(evaluation, CandidateEvaluation)
            for evaluation in self.evaluations
        ):
            raise TypeError("evaluations must contain only CandidateEvaluation values.")
        if self.progress is None:
            object.__setattr__(
                self,
                "progress",
                OptimizationProgress(len(self.evaluations), len(self.evaluations)),
            )
        if not isinstance(self.progress, OptimizationProgress):
            raise TypeError("progress must be an OptimizationProgress.")
        if self.progress.evaluated_candidates != len(self.evaluations):
            raise ValueError("progress must match the evaluation count.")
