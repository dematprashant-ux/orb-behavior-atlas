"""Read-only immutable projections and collections of optimization run state."""

from collections.abc import Iterable, Iterator
from dataclasses import dataclass

from src.engines.backtesting.selection import ObjectiveSelection
from src.engines.backtesting.strategy_metadata import OptimizationStrategyMetadata
from src.engines.backtesting.termination import OptimizationTerminationReason

__all__ = [
    "OptimizationRunSummaries",
    "OptimizationRunSummary",
    "OptimizationRunSummaryAggregate",
    "OptimizationRunSummaryAnalysis",
    "OptimizationRunSummaryCatalog",
    "OptimizationRunSummaryComparison",
    "OptimizationRunSummaryDelta",
    "OptimizationRunSummaryReport",
    "OptimizationResultReport",
    "OptimizationRunSummaryRates",
]


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


@dataclass(frozen=True, slots=True)
class OptimizationRunSummaryAggregate:
    """Retain scalar totals derived from one summary collection without analysis."""

    run_count: int
    evaluated_candidate_count: int
    total_eligible_candidate_count: int
    recorded_rejection_count: int
    search_space_exhausted_count: int
    evaluation_budget_reached_count: int

    def __post_init__(self) -> None:
        """Require non-negative deterministic integer totals only."""
        for value, name in (
            (self.run_count, "run_count"),
            (self.evaluated_candidate_count, "evaluated_candidate_count"),
            (self.total_eligible_candidate_count, "total_eligible_candidate_count"),
            (self.recorded_rejection_count, "recorded_rejection_count"),
            (self.search_space_exhausted_count, "search_space_exhausted_count"),
            (
                self.evaluation_budget_reached_count,
                "evaluation_budget_reached_count",
            ),
        ):
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an int.")
            if value < 0:
                raise ValueError(f"{name} must not be negative.")
        if (
            self.search_space_exhausted_count
            + self.evaluation_budget_reached_count
            != self.run_count
        ):
            raise ValueError("termination counts must match run_count.")

    @classmethod
    def from_summaries(
        cls,
        summaries: OptimizationRunSummaries,
    ) -> "OptimizationRunSummaryAggregate":
        """Derive scalar totals from one existing immutable summary collection."""
        if not isinstance(summaries, OptimizationRunSummaries):
            raise TypeError("summaries must be an OptimizationRunSummaries.")

        run_count = 0
        evaluated_candidate_count = 0
        total_eligible_candidate_count = 0
        recorded_rejection_count = 0
        search_space_exhausted_count = 0
        evaluation_budget_reached_count = 0
        for summary in summaries:
            run_count += 1
            evaluated_candidate_count += summary.evaluated_candidate_count
            total_eligible_candidate_count += summary.total_eligible_candidate_count
            recorded_rejection_count += summary.rejection_count
            if (
                summary.termination_reason
                is OptimizationTerminationReason.SEARCH_SPACE_EXHAUSTED
            ):
                search_space_exhausted_count += 1
            elif (
                summary.termination_reason
                is OptimizationTerminationReason.EVALUATION_BUDGET_REACHED
            ):
                evaluation_budget_reached_count += 1
            else:
                raise ValueError("summary has an unsupported termination reason.")

        return cls(
            run_count,
            evaluated_candidate_count,
            total_eligible_candidate_count,
            recorded_rejection_count,
            search_space_exhausted_count,
            evaluation_budget_reached_count,
        )


@dataclass(frozen=True, slots=True)
class OptimizationRunSummaryRates:
    """Retain scalar rates derived only from an existing summary aggregate."""

    candidate_completion_rate: float
    recorded_rejection_rate: float
    search_space_exhausted_rate: float
    evaluation_budget_reached_rate: float

    def __post_init__(self) -> None:
        """Require finite probability-like float values without formatting."""
        for value, name in (
            (self.candidate_completion_rate, "candidate_completion_rate"),
            (self.recorded_rejection_rate, "recorded_rejection_rate"),
            (self.search_space_exhausted_rate, "search_space_exhausted_rate"),
            (
                self.evaluation_budget_reached_rate,
                "evaluation_budget_reached_rate",
            ),
        ):
            if not isinstance(value, float):
                raise TypeError(f"{name} must be a float.")
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0.0 and 1.0.")

    @classmethod
    def from_aggregate(
        cls,
        aggregate: OptimizationRunSummaryAggregate,
    ) -> "OptimizationRunSummaryRates":
        """Derive deterministic float rates from aggregate scalar totals only."""
        if not isinstance(aggregate, OptimizationRunSummaryAggregate):
            raise TypeError("aggregate must be an OptimizationRunSummaryAggregate.")
        return cls(
            candidate_completion_rate=_rate(
                aggregate.evaluated_candidate_count,
                aggregate.total_eligible_candidate_count,
            ),
            recorded_rejection_rate=_rate(
                aggregate.recorded_rejection_count,
                (
                    aggregate.evaluated_candidate_count
                    + aggregate.recorded_rejection_count
                ),
            ),
            search_space_exhausted_rate=_rate(
                aggregate.search_space_exhausted_count,
                aggregate.run_count,
            ),
            evaluation_budget_reached_rate=_rate(
                aggregate.evaluation_budget_reached_count,
                aggregate.run_count,
            ),
        )


@dataclass(frozen=True, slots=True)
class OptimizationRunSummaryAnalysis:
    """Retain canonical summary collection, aggregate, and rates by identity."""

    summaries: OptimizationRunSummaries
    aggregate: OptimizationRunSummaryAggregate
    rates: OptimizationRunSummaryRates

    def __post_init__(self) -> None:
        """Require existing immutable analytical components without recalculation."""
        if not isinstance(self.summaries, OptimizationRunSummaries):
            raise TypeError("summaries must be an OptimizationRunSummaries.")
        if not isinstance(self.aggregate, OptimizationRunSummaryAggregate):
            raise TypeError("aggregate must be an OptimizationRunSummaryAggregate.")
        if not isinstance(self.rates, OptimizationRunSummaryRates):
            raise TypeError("rates must be an OptimizationRunSummaryRates.")

    @classmethod
    def from_summaries(
        cls,
        summaries: OptimizationRunSummaries,
    ) -> "OptimizationRunSummaryAnalysis":
        """Compose canonical aggregate and rates values from existing summaries."""
        if not isinstance(summaries, OptimizationRunSummaries):
            raise TypeError("summaries must be an OptimizationRunSummaries.")
        aggregate = OptimizationRunSummaryAggregate.from_summaries(summaries)
        rates = OptimizationRunSummaryRates.from_aggregate(aggregate)
        return cls(summaries, aggregate, rates)


@dataclass(frozen=True, slots=True)
class OptimizationRunSummaryDelta:
    """Describe scalar directional differences between two summary analyses."""

    run_count_delta: int
    evaluated_candidate_count_delta: int
    total_eligible_candidate_count_delta: int
    recorded_rejection_count_delta: int
    search_space_exhausted_count_delta: int
    evaluation_budget_reached_count_delta: int
    candidate_completion_rate_delta: float
    recorded_rejection_rate_delta: float
    search_space_exhausted_rate_delta: float
    evaluation_budget_reached_rate_delta: float

    def __post_init__(self) -> None:
        """Require signed scalar differences without interpreting their direction."""
        for value, name in (
            (self.run_count_delta, "run_count_delta"),
            (self.evaluated_candidate_count_delta, "evaluated_candidate_count_delta"),
            (
                self.total_eligible_candidate_count_delta,
                "total_eligible_candidate_count_delta",
            ),
            (self.recorded_rejection_count_delta, "recorded_rejection_count_delta"),
            (
                self.search_space_exhausted_count_delta,
                "search_space_exhausted_count_delta",
            ),
            (
                self.evaluation_budget_reached_count_delta,
                "evaluation_budget_reached_count_delta",
            ),
        ):
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an int.")
        for value, name in (
            (self.candidate_completion_rate_delta, "candidate_completion_rate_delta"),
            (self.recorded_rejection_rate_delta, "recorded_rejection_rate_delta"),
            (
                self.search_space_exhausted_rate_delta,
                "search_space_exhausted_rate_delta",
            ),
            (
                self.evaluation_budget_reached_rate_delta,
                "evaluation_budget_reached_rate_delta",
            ),
        ):
            if not isinstance(value, float):
                raise TypeError(f"{name} must be a float.")
            if not -1.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between -1.0 and 1.0.")

    @classmethod
    def between(
        cls,
        baseline: OptimizationRunSummaryAnalysis,
        comparison: OptimizationRunSummaryAnalysis,
    ) -> "OptimizationRunSummaryDelta":
        """Calculate comparison-minus-baseline scalar differences only."""
        if not isinstance(baseline, OptimizationRunSummaryAnalysis):
            raise TypeError("baseline must be an OptimizationRunSummaryAnalysis.")
        if not isinstance(comparison, OptimizationRunSummaryAnalysis):
            raise TypeError("comparison must be an OptimizationRunSummaryAnalysis.")
        return cls(
            run_count_delta=(
                comparison.aggregate.run_count - baseline.aggregate.run_count
            ),
            evaluated_candidate_count_delta=(
                comparison.aggregate.evaluated_candidate_count
                - baseline.aggregate.evaluated_candidate_count
            ),
            total_eligible_candidate_count_delta=(
                comparison.aggregate.total_eligible_candidate_count
                - baseline.aggregate.total_eligible_candidate_count
            ),
            recorded_rejection_count_delta=(
                comparison.aggregate.recorded_rejection_count
                - baseline.aggregate.recorded_rejection_count
            ),
            search_space_exhausted_count_delta=(
                comparison.aggregate.search_space_exhausted_count
                - baseline.aggregate.search_space_exhausted_count
            ),
            evaluation_budget_reached_count_delta=(
                comparison.aggregate.evaluation_budget_reached_count
                - baseline.aggregate.evaluation_budget_reached_count
            ),
            candidate_completion_rate_delta=(
                comparison.rates.candidate_completion_rate
                - baseline.rates.candidate_completion_rate
            ),
            recorded_rejection_rate_delta=(
                comparison.rates.recorded_rejection_rate
                - baseline.rates.recorded_rejection_rate
            ),
            search_space_exhausted_rate_delta=(
                comparison.rates.search_space_exhausted_rate
                - baseline.rates.search_space_exhausted_rate
            ),
            evaluation_budget_reached_rate_delta=(
                comparison.rates.evaluation_budget_reached_rate
                - baseline.rates.evaluation_budget_reached_rate
            ),
        )


@dataclass(frozen=True, slots=True)
class OptimizationRunSummaryComparison:
    """Retain two summary analyses and their canonical directional delta."""

    baseline: OptimizationRunSummaryAnalysis
    comparison: OptimizationRunSummaryAnalysis
    delta: OptimizationRunSummaryDelta

    def __post_init__(self) -> None:
        """Require existing immutable components without recalculation."""
        if not isinstance(self.baseline, OptimizationRunSummaryAnalysis):
            raise TypeError("baseline must be an OptimizationRunSummaryAnalysis.")
        if not isinstance(self.comparison, OptimizationRunSummaryAnalysis):
            raise TypeError("comparison must be an OptimizationRunSummaryAnalysis.")
        if not isinstance(self.delta, OptimizationRunSummaryDelta):
            raise TypeError("delta must be an OptimizationRunSummaryDelta.")

    @classmethod
    def between(
        cls,
        baseline: OptimizationRunSummaryAnalysis,
        comparison: OptimizationRunSummaryAnalysis,
    ) -> "OptimizationRunSummaryComparison":
        """Compose two retained analyses with their canonical delta only."""
        if not isinstance(baseline, OptimizationRunSummaryAnalysis):
            raise TypeError("baseline must be an OptimizationRunSummaryAnalysis.")
        if not isinstance(comparison, OptimizationRunSummaryAnalysis):
            raise TypeError("comparison must be an OptimizationRunSummaryAnalysis.")
        delta = OptimizationRunSummaryDelta.between(baseline, comparison)
        return cls(baseline, comparison, delta)


@dataclass(frozen=True, slots=True)
class OptimizationRunSummaryCatalog:
    """Retain ordered existing summary comparisons without interpretation."""

    comparisons: tuple[OptimizationRunSummaryComparison, ...]

    def __post_init__(self) -> None:
        """Normalize one iterable into immutable ordered comparison storage."""
        try:
            comparisons = tuple(self.comparisons)
        except TypeError as error:
            raise TypeError(
                "comparisons must be an iterable of OptimizationRunSummaryComparison "
                "values."
            ) from error
        if any(
            not isinstance(comparison, OptimizationRunSummaryComparison)
            for comparison in comparisons
        ):
            raise TypeError(
                "comparisons must contain only OptimizationRunSummaryComparison "
                "values."
            )
        object.__setattr__(self, "comparisons", comparisons)

    def __iter__(self) -> Iterator[OptimizationRunSummaryComparison]:
        """Iterate over retained comparisons in exact insertion order."""
        return iter(self.comparisons)

    def __len__(self) -> int:
        """Return the number of retained comparisons without calculation."""
        return len(self.comparisons)

    def __getitem__(self, index: int) -> OptimizationRunSummaryComparison:
        """Return one retained comparison by zero-based insertion position."""
        return self.comparisons[index]


@dataclass(frozen=True, slots=True)
class OptimizationRunSummaryReport:
    """Retain one canonical summary analysis as structured report-domain data."""

    analysis: OptimizationRunSummaryAnalysis

    def __post_init__(self) -> None:
        """Require one existing immutable analysis without reconstruction."""
        if not isinstance(self.analysis, OptimizationRunSummaryAnalysis):
            raise TypeError("analysis must be an OptimizationRunSummaryAnalysis.")

    @classmethod
    def from_analysis(
        cls,
        analysis: OptimizationRunSummaryAnalysis,
    ) -> "OptimizationRunSummaryReport":
        """Construct a report that retains the supplied analysis by identity."""
        if not isinstance(analysis, OptimizationRunSummaryAnalysis):
            raise TypeError("analysis must be an OptimizationRunSummaryAnalysis.")
        return cls(analysis)


@dataclass(frozen=True, slots=True)
class OptimizationResultReport:
    """Retain one completed run and its canonical selection by identity."""

    run: "OptimizationRun"
    selection: ObjectiveSelection

    def __post_init__(self) -> None:
        """Require the selection to retain the exact ranking owned by the run."""
        from src.engines.backtesting.optimization import OptimizationRun

        if not isinstance(self.run, OptimizationRun):
            raise TypeError("run must be an OptimizationRun.")
        if not isinstance(self.selection, ObjectiveSelection):
            raise TypeError("selection must be an ObjectiveSelection.")
        if self.selection.ranking is not self.run.ranking:
            raise ValueError("selection must reference the run's exact ranking.")

    @classmethod
    def from_run_and_selection(
        cls,
        run: "OptimizationRun",
        selection: ObjectiveSelection,
    ) -> "OptimizationResultReport":
        """Construct a read-only result report without rerunning any stage."""
        return cls(run, selection)


def _rate(numerator: int, denominator: int) -> float:
    """Return the established deterministic zero-denominator float ratio."""
    if denominator == 0:
        return 0.0
    if numerator > denominator:
        raise ValueError("rate numerator must not exceed its denominator.")
    return numerator / denominator
