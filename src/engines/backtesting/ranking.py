"""Deterministic single-objective ranking over completed objective scores."""

from dataclasses import dataclass
from typing import Protocol

from src.engines.backtesting.objectives import ObjectiveDirection, ObjectiveScore

__all__ = [
    "ObjectiveRanker",
    "ObjectiveRanking",
    "RankedObjectiveScore",
    "StandardObjectiveRanker",
]


@dataclass(frozen=True, slots=True)
class RankedObjectiveScore:
    """Retain one objective score with its one-based completed ranking position."""

    source_score: ObjectiveScore
    rank: int

    def __post_init__(self) -> None:
        """Require a typed score and a strictly positive non-boolean rank."""
        if not isinstance(self.source_score, ObjectiveScore):
            raise TypeError("source_score must be an ObjectiveScore.")
        if isinstance(self.rank, bool) or not isinstance(self.rank, int):
            raise TypeError("rank must be an int.")
        if self.rank <= 0:
            raise ValueError("rank must be positive.")


@dataclass(frozen=True, slots=True)
class ObjectiveRanking:
    """Retain one direction and its complete ordered immutable ranked scores."""

    direction: ObjectiveDirection
    ranked_scores: tuple[RankedObjectiveScore, ...] = ()

    def __post_init__(self) -> None:
        """Require direction-consistent contiguous ranks without selecting a winner."""
        if not isinstance(self.direction, ObjectiveDirection):
            raise TypeError("direction must be an ObjectiveDirection.")
        if not isinstance(self.ranked_scores, tuple):
            raise TypeError(
                "ranked_scores must be a tuple of RankedObjectiveScore values."
            )
        if any(
            not isinstance(ranked_score, RankedObjectiveScore)
            for ranked_score in self.ranked_scores
        ):
            raise TypeError(
                "ranked_scores must contain only RankedObjectiveScore values."
            )
        if any(
            ranked_score.source_score.direction is not self.direction
            for ranked_score in self.ranked_scores
        ):
            raise ValueError("ranked_scores must match the ranking direction.")
        expected_ranks = tuple(range(1, len(self.ranked_scores) + 1))
        actual_ranks = tuple(ranked_score.rank for ranked_score in self.ranked_scores)
        if actual_ranks != expected_ranks:
            raise ValueError("ranked_scores must have contiguous ranks in order.")


class ObjectiveRanker(Protocol):
    """Define deterministic score ordering without selection or scoring behavior."""

    def rank(self, scores: tuple[ObjectiveScore, ...]) -> ObjectiveRanking:
        """Return a complete immutable order for scores sharing one direction."""


@dataclass(frozen=True, slots=True)
class StandardObjectiveRanker:
    """Order scores by one injected direction while preserving equal-score order."""

    direction: ObjectiveDirection

    def __post_init__(self) -> None:
        """Require an explicit objective direction, including for empty rankings."""
        if not isinstance(self.direction, ObjectiveDirection):
            raise TypeError("direction must be an ObjectiveDirection.")

    def rank(self, scores: tuple[ObjectiveScore, ...]) -> ObjectiveRanking:
        """Rank complete scores in stable value order without a selection policy."""
        if not isinstance(scores, tuple):
            raise TypeError("scores must be a tuple of ObjectiveScore values.")
        if any(not isinstance(score, ObjectiveScore) for score in scores):
            raise TypeError("scores must contain only ObjectiveScore values.")
        if any(score.direction is not self.direction for score in scores):
            raise ValueError("scores must match the ranker direction.")

        ordered_scores = tuple(
            sorted(
                scores,
                key=lambda score: score.score,
                reverse=self.direction is ObjectiveDirection.MAXIMIZE,
            )
        )
        return ObjectiveRanking(
            direction=self.direction,
            ranked_scores=tuple(
                RankedObjectiveScore(source_score=score, rank=index)
                for index, score in enumerate(ordered_scores, start=1)
            ),
        )
