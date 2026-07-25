"""Deterministic composition of existing search, scoring, ranking, and selection."""

from dataclasses import dataclass
from typing import Protocol

from src.engines.backtesting.configuration import OptimizationConfiguration
from src.engines.backtesting.evaluation import CandidateEvaluation
from src.engines.backtesting.grid_search import GridSearchRun
from src.engines.backtesting.objectives import CandidateObjective, ObjectiveScore
from src.engines.backtesting.ranking import ObjectiveRanker, ObjectiveRanking
from src.engines.backtesting.selection import ObjectiveSelection
from src.engines.backtesting.specification import OptimizationSpecification
from src.engines.backtesting.strategies import OptimizationStrategy

__all__ = ["OptimizationRun", "OptimizationRunner", "StandardOptimizationRunner"]


@dataclass(frozen=True, slots=True)
class OptimizationRun:
    """Retain one complete immutable search-to-selection orchestration result."""

    grid_search_run: GridSearchRun
    objective_scores: tuple[ObjectiveScore, ...]
    ranking: ObjectiveRanking
    selection: ObjectiveSelection

    def __post_init__(self) -> None:
        """Require exact cross-stage references without recomputing any result."""
        if not isinstance(self.grid_search_run, GridSearchRun):
            raise TypeError("grid_search_run must be a GridSearchRun.")
        if not isinstance(self.objective_scores, tuple):
            raise TypeError(
                "objective_scores must be a tuple of ObjectiveScore values."
            )
        if any(
            not isinstance(score, ObjectiveScore) for score in self.objective_scores
        ):
            raise TypeError("objective_scores must contain only ObjectiveScore values.")
        if not isinstance(self.ranking, ObjectiveRanking):
            raise TypeError("ranking must be an ObjectiveRanking.")
        if not isinstance(self.selection, ObjectiveSelection):
            raise TypeError("selection must be an ObjectiveSelection.")
        if not _same_references(
            tuple(score.evaluation for score in self.objective_scores),
            self.grid_search_run.evaluations,
        ):
            raise ValueError(
                "objective_scores must reference grid search evaluations in order."
            )
        if not _same_references_regardless_of_order(
            tuple(
                ranked_score.source_score for ranked_score in self.ranking.ranked_scores
            ),
            self.objective_scores,
        ):
            raise ValueError("ranking must contain exactly the objective scores.")
        if self.selection.ranking is not self.ranking:
            raise ValueError("selection must reference the exact ranking.")


class OptimizationRunner(Protocol):
    """Define deterministic optimization orchestration without optimizer heuristics."""

    def run(self, specification: OptimizationSpecification) -> OptimizationRun:
        """Return complete search, scoring, ranking, and selection artifacts."""


@dataclass(frozen=True, slots=True)
class StandardOptimizationRunner:
    """Coordinate injected optimization collaborators in one deterministic order."""

    optimization_strategy: OptimizationStrategy
    candidate_objective: CandidateObjective
    objective_ranker: ObjectiveRanker

    def __post_init__(self) -> None:
        """Require explicit collaborators without inspecting or invoking them."""
        for collaborator, name in (
            (self.optimization_strategy, "optimization_strategy"),
            (self.candidate_objective, "candidate_objective"),
            (self.objective_ranker, "objective_ranker"),
        ):
            if collaborator is None:
                raise TypeError(f"{name} must not be None.")

    def run(self, specification: OptimizationSpecification) -> OptimizationRun:
        """Delegate once through search, score, rank, and selection stages."""
        if not isinstance(specification, OptimizationSpecification):
            raise TypeError("specification must be an OptimizationSpecification.")
        configuration = specification.configuration
        grid_search_run = self.optimization_strategy.execute(specification)
        if not isinstance(grid_search_run, GridSearchRun):
            raise TypeError(
                "optimization_strategy.execute must return a GridSearchRun."
            )
        if grid_search_run.parameter_space is not specification.parameter_space:
            raise ValueError("grid_search_run must retain the source parameter_space.")

        objective_scores = tuple(
            self._score_evaluation(evaluation, configuration)
            for evaluation in grid_search_run.evaluations
        )
        ranking = self.objective_ranker.rank(objective_scores)
        if not isinstance(ranking, ObjectiveRanking):
            raise TypeError("objective_ranker.rank must return an ObjectiveRanking.")
        if ranking.direction is not configuration.direction:
            raise ValueError(
                "ranking direction must match the configuration direction."
            )
        selection = configuration.selection_policy.select(ranking)
        if not isinstance(selection, ObjectiveSelection):
            raise TypeError(
                "selection_policy.select must return an ObjectiveSelection."
            )

        return OptimizationRun(grid_search_run, objective_scores, ranking, selection)

    def _score_evaluation(
        self,
        evaluation: CandidateEvaluation,
        configuration: OptimizationConfiguration,
    ) -> ObjectiveScore:
        """Score one search evaluation while enforcing its exact source reference."""
        score = self.candidate_objective.score(evaluation)
        if not isinstance(score, ObjectiveScore):
            raise TypeError("candidate_objective.score must return an ObjectiveScore.")
        if score.evaluation is not evaluation:
            raise ValueError("objective score must reference its source evaluation.")
        if score.direction is not configuration.direction:
            raise ValueError("objective score direction must match the configuration.")
        return score


def _same_references(left: tuple[object, ...], right: tuple[object, ...]) -> bool:
    """Return whether two ordered tuples contain the same object references."""
    return len(left) == len(right) and all(
        left_item is right_item for left_item, right_item in zip(left, right)
    )


def _same_references_regardless_of_order(
    left: tuple[object, ...],
    right: tuple[object, ...],
) -> bool:
    """Return whether two tuples contain each object reference exactly once."""
    if len(left) != len(right):
        return False
    remaining = list(right)
    for left_item in left:
        for index, right_item in enumerate(remaining):
            if left_item is right_item:
                del remaining[index]
                break
        else:
            return False
    return not remaining
