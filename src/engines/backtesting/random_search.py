"""Random-search orchestration over injected sampling and evaluation contracts."""

from dataclasses import dataclass, field

from src.engines.backtesting.evaluation import CandidateEvaluation
from src.engines.backtesting.interfaces import CandidateEvaluator
from src.engines.backtesting.random_sampling import (
    RandomCandidateSampler,
    RandomOptimizationConfiguration,
)
from src.engines.backtesting.progress import OptimizationProgress
from src.engines.backtesting.search import OptimizationSearchRun
from src.engines.backtesting.specification import OptimizationSpecification
from src.engines.backtesting.strategy_metadata import OptimizationStrategyMetadata
from src.engines.backtesting.termination import OptimizationTerminationReason

__all__ = ["RandomOptimizationConfiguration", "RandomOptimizationStrategy"]


@dataclass(frozen=True, slots=True)
class RandomOptimizationStrategy:
    """Coordinate injected random sampling and candidate evaluation once each."""

    random_candidate_sampler: RandomCandidateSampler
    candidate_evaluator: CandidateEvaluator
    configuration: RandomOptimizationConfiguration
    metadata: OptimizationStrategyMetadata = field(
        default=OptimizationStrategyMetadata("random"),
        init=False,
    )

    def __post_init__(self) -> None:
        """Require injected collaborators and explicit sampling configuration."""
        if self.random_candidate_sampler is None:
            raise TypeError("random_candidate_sampler must not be None.")
        if self.candidate_evaluator is None:
            raise TypeError("candidate_evaluator must not be None.")
        if not isinstance(self.configuration, RandomOptimizationConfiguration):
            raise TypeError("configuration must be a RandomOptimizationConfiguration.")

    def execute(
        self,
        specification: OptimizationSpecification,
    ) -> OptimizationSearchRun:
        """Evaluate sampled candidates without scoring, ranking, or selection."""
        if not isinstance(specification, OptimizationSpecification):
            raise TypeError("specification must be an OptimizationSpecification.")
        candidates = self.random_candidate_sampler.sample(
            specification.parameter_space,
            self.configuration,
        )
        eligible_candidates = tuple(
            candidate
            for candidate in candidates
            if specification.constraints.is_eligible(candidate)
        )
        evaluations: list[CandidateEvaluation] = []
        for candidate in eligible_candidates[: specification.budget.maximum_evaluations]:
            evaluation = self.candidate_evaluator.evaluate(candidate)
            if not isinstance(evaluation, CandidateEvaluation):
                raise TypeError(
                    "candidate_evaluator.evaluate must return a CandidateEvaluation."
                )
            if evaluation.candidate is not candidate:
                raise ValueError("evaluation candidate must match sampled candidate.")
            evaluations.append(evaluation)
        total_candidates = len(eligible_candidates)
        progress = OptimizationProgress(len(evaluations), total_candidates)
        termination_reason = (
            OptimizationTerminationReason.SEARCH_SPACE_EXHAUSTED
            if progress.evaluated_candidates == progress.total_candidates
            else OptimizationTerminationReason.EVALUATION_BUDGET_REACHED
        )
        return OptimizationSearchRun(
            self.metadata,
            tuple(evaluations),
            progress,
            termination_reason,
        )
