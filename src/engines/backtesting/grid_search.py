"""Deterministic orchestration of existing candidate generation and evaluation."""

from dataclasses import dataclass
from typing import Protocol

from src.engines.backtesting.budget import OptimizationBudget
from src.engines.backtesting.evaluation import CandidateEvaluation
from src.engines.backtesting.interfaces import CandidateEvaluator
from src.engines.strategy.interfaces import CandidateGenerator
from src.engines.strategy.parameters import CandidateParameterSet, ParameterSpace

__all__ = ["GridSearchRun", "GridSearchRunner", "StandardGridSearchRunner"]


@dataclass(frozen=True, slots=True)
class GridSearchRun:
    """Retain one source space and its generated-order evaluation results."""

    parameter_space: ParameterSpace
    evaluations: tuple[CandidateEvaluation, ...] = ()

    def __post_init__(self) -> None:
        """Require immutable typed aggregate values without ranking them."""
        if not isinstance(self.parameter_space, ParameterSpace):
            raise TypeError("parameter_space must be a ParameterSpace.")
        if not isinstance(self.evaluations, tuple):
            raise TypeError(
                "evaluations must be a tuple of CandidateEvaluation values."
            )
        if any(
            not isinstance(evaluation, CandidateEvaluation)
            for evaluation in self.evaluations
        ):
            raise TypeError("evaluations must contain only CandidateEvaluation values.")


class GridSearchRunner(Protocol):
    """Define deterministic candidate orchestration without optimization logic."""

    def run(
        self,
        parameter_space: ParameterSpace,
        budget: OptimizationBudget,
    ) -> GridSearchRun:
        """Generate and evaluate source-order candidates within one budget."""


@dataclass(frozen=True, slots=True)
class StandardGridSearchRunner:
    """Compose injected generation and evaluation collaborators sequentially."""

    candidate_generator: CandidateGenerator
    candidate_evaluator: CandidateEvaluator

    def __post_init__(self) -> None:
        """Require explicit collaborators without inspecting or invoking them."""
        if self.candidate_generator is None:
            raise TypeError("candidate_generator must not be None.")
        if self.candidate_evaluator is None:
            raise TypeError("candidate_evaluator must not be None.")

    def run(
        self,
        parameter_space: ParameterSpace,
        budget: OptimizationBudget,
    ) -> GridSearchRun:
        """Evaluate every generated candidate once in generation order.

        Collaborator exceptions intentionally propagate unchanged. A run is only
        constructed after every generated candidate has a consistent evaluation,
        so no partial result can be returned.
        """
        if not isinstance(parameter_space, ParameterSpace):
            raise TypeError("parameter_space must be a ParameterSpace.")
        if not isinstance(budget, OptimizationBudget):
            raise TypeError("budget must be an OptimizationBudget.")

        candidates = self.candidate_generator.generate(parameter_space)
        if not isinstance(candidates, tuple):
            raise TypeError(
                "candidate_generator.generate must return a tuple of "
                "CandidateParameterSet values."
            )
        if any(
            not isinstance(candidate, CandidateParameterSet)
            for candidate in candidates
        ):
            raise TypeError(
                "candidate_generator.generate must return only "
                "CandidateParameterSet values."
            )

        evaluations: list[CandidateEvaluation] = []
        for candidate in candidates[: budget.maximum_evaluations]:
            evaluation = self.candidate_evaluator.evaluate(candidate)
            if not isinstance(evaluation, CandidateEvaluation):
                raise TypeError(
                    "candidate_evaluator.evaluate must return a "
                    "CandidateEvaluation."
                )
            if evaluation.candidate is not candidate:
                raise ValueError("evaluation candidate must match generated candidate.")
            evaluations.append(evaluation)

        return GridSearchRun(parameter_space, tuple(evaluations))
