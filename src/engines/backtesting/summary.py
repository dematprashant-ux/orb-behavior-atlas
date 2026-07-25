"""Read-only immutable projections and collections of optimization run state."""

from collections.abc import Iterable, Iterator
from dataclasses import dataclass

from src.engines.backtesting.strategy_metadata import OptimizationStrategyMetadata
from src.engines.backtesting.termination import OptimizationTerminationReason

__all__ = ["OptimizationRunSummaries", "OptimizationRunSummary"]


@dataclass(frozen=True, slots=True)
class OptimizationRunSummary:
    """Describe existing successful optimization facts without re-execution."""

    strategy_metadata: OptimizationStrategyMetadata
    evaluated_candidate_count: int
    total_eligible_candidate_count: int
    completion_ratio: float
    termination_reason: OptimizationTerminationReason
    rejection_count: int

    def __post_init__(self) -> None:
        """Require immutable typed facts consistent with progress semantics."""
        if not isinstance(self.strategy_metadata, OptimizationStrategyMetadata):
            raise TypeError(
                "strategy_metadata must be an OptimizationStrategyMetadata."
            )
        for value, name in (
            (self.evaluated_candidate_count, "evaluated_candidate_count"),
            (self.total_eligible_candidate_count, "total_eligible_candidate_count"),
            (self.rejection_count, "rejection_count"),
        ):
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an int.")
            if value < 0:
                raise ValueError(f"{name} must not be negative.")
        if self.evaluated_candidate_count > self.total_eligible_candidate_count:
            raise ValueError(
                "evaluated_candidate_count must not exceed "
                "total_eligible_candidate_count."
            )
        if not isinstance(self.completion_ratio, float):
            raise TypeError("completion_ratio must be a float.")
        if not isinstance(self.termination_reason, OptimizationTerminationReason):
            raise TypeError(
                "termination_reason must be an OptimizationTerminationReason."
            )

    @classmethod
    def from_run(cls, run: "OptimizationRun") -> "OptimizationRunSummary":
        """Project one completed run without invoking any execution collaborator."""
        from src.engines.backtesting.optimization import OptimizationRun

        if not isinstance(run, OptimizationRun):
            raise TypeError("run must be an OptimizationRun.")
        return cls(
            strategy_metadata=run.strategy_metadata,
            evaluated_candidate_count=run.progress.evaluated_candidates,
            total_eligible_candidate_count=run.progress.total_candidates,
            completion_ratio=run.progress.completion_ratio,
            termination_reason=run.termination_reason,
            rejection_count=len(run.constraint_diagnostics.rejections),
        )


@dataclass(frozen=True, slots=True)
class OptimizationRunSummaries:
    """Retain ordered existing optimization summaries without aggregation."""

    summaries: tuple[OptimizationRunSummary, ...]

    def __post_init__(self) -> None:
        """Normalize one supplied iterable into immutable ordered summary storage."""
        try:
            summaries = tuple(self.summaries)
        except TypeError as error:
            raise TypeError(
                "summaries must be an iterable of OptimizationRunSummary values."
            ) from error
        if any(
            not isinstance(summary, OptimizationRunSummary) for summary in summaries
        ):
            raise TypeError(
                "summaries must contain only OptimizationRunSummary values."
            )
        object.__setattr__(self, "summaries", summaries)

    def __iter__(self) -> Iterator[OptimizationRunSummary]:
        """Iterate over supplied summaries in their exact insertion order."""
        return iter(self.summaries)

    def __len__(self) -> int:
        """Return the number of retained summaries without aggregation."""
        return len(self.summaries)

    def __getitem__(self, index: int) -> OptimizationRunSummary:
        """Return one supplied summary by its zero-based insertion position."""
        return self.summaries[index]
