"""Typed objective-scoring contracts for future candidate selection."""

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import Protocol

from src.engines.backtesting.evaluation import CandidateEvaluation

__all__ = ["CandidateObjective", "ObjectiveDirection", "ObjectiveScore"]


class ObjectiveDirection(str, Enum):
    """Identify whether a future selection process prefers higher or lower scores."""

    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"


@dataclass(frozen=True, slots=True)
class ObjectiveScore:
    """Retain one candidate evaluation with its finite directional scalar score."""

    evaluation: CandidateEvaluation
    score: float
    direction: ObjectiveDirection

    def __post_init__(self) -> None:
        """Require typed references and normalize finite numeric scores to float."""
        if not isinstance(self.evaluation, CandidateEvaluation):
            raise TypeError("evaluation must be a CandidateEvaluation.")
        if isinstance(self.score, bool) or not isinstance(self.score, (int, float)):
            raise TypeError("score must be an int or float.")
        try:
            normalized_score = float(self.score)
        except OverflowError as error:
            raise ValueError("score must be finite.") from error
        if not isfinite(normalized_score):
            raise ValueError("score must be finite.")
        object.__setattr__(self, "score", normalized_score)
        if not isinstance(self.direction, ObjectiveDirection):
            raise TypeError("direction must be an ObjectiveDirection.")


class CandidateObjective(Protocol):
    """Define injected scalar scoring without ranking or selection behavior."""

    def score(self, evaluation: CandidateEvaluation) -> ObjectiveScore:
        """Return one finite directional score for an existing evaluation."""
