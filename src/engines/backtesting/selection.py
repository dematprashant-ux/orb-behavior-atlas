"""Deterministic policies that select entries from completed objective rankings."""

from dataclasses import dataclass
from typing import Protocol

from src.engines.backtesting.ranking import ObjectiveRanking, RankedObjectiveScore

__all__ = [
    "BestRankSelectionPolicy",
    "ObjectiveSelection",
    "SelectionPolicy",
    "TopRankedSelectionPolicy",
]


@dataclass(frozen=True, slots=True)
class ObjectiveSelection:
    """Retain one source ranking with an ordered immutable selected subsequence."""

    ranking: ObjectiveRanking
    selected_scores: tuple[RankedObjectiveScore, ...] = ()

    def __post_init__(self) -> None:
        """Require source-owned unique entries in their original ranking order."""
        if not isinstance(self.ranking, ObjectiveRanking):
            raise TypeError("ranking must be an ObjectiveRanking.")
        if not isinstance(self.selected_scores, tuple):
            raise TypeError(
                "selected_scores must be a tuple of RankedObjectiveScore values."
            )
        if any(
            not isinstance(selected_score, RankedObjectiveScore)
            for selected_score in self.selected_scores
        ):
            raise TypeError(
                "selected_scores must contain only RankedObjectiveScore values."
            )

        source_positions = tuple(
            _source_position(selected_score, self.ranking.ranked_scores)
            for selected_score in self.selected_scores
        )
        if any(position is None for position in source_positions):
            raise ValueError("selected_scores must come from the source ranking.")
        resolved_positions = tuple(
            position for position in source_positions if position is not None
        )
        if len(set(resolved_positions)) != len(resolved_positions):
            raise ValueError("selected_scores must not contain duplicate entries.")
        if resolved_positions != tuple(sorted(resolved_positions)):
            raise ValueError("selected_scores must preserve source ranking order.")


class SelectionPolicy(Protocol):
    """Define selection from completed rankings without altering their order."""

    def select(self, ranking: ObjectiveRanking) -> ObjectiveSelection:
        """Return an immutable source-ordered selection without reranking."""


@dataclass(frozen=True, slots=True)
class BestRankSelectionPolicy:
    """Select all entries tied at the leading score of a completed ranking."""

    def select(self, ranking: ObjectiveRanking) -> ObjectiveSelection:
        """Return leading-score ties, or an empty selection for an empty ranking."""
        if not isinstance(ranking, ObjectiveRanking):
            raise TypeError("ranking must be an ObjectiveRanking.")
        if not ranking.ranked_scores:
            return ObjectiveSelection(ranking)

        best_score = ranking.ranked_scores[0].source_score.score
        return ObjectiveSelection(
            ranking,
            tuple(
                ranked_score
                for ranked_score in ranking.ranked_scores
                if ranked_score.source_score.score == best_score
            ),
        )


@dataclass(frozen=True, slots=True)
class TopRankedSelectionPolicy:
    """Select one explicit count of leading positional entries from a ranking."""

    count: int

    def __post_init__(self) -> None:
        """Require a strictly positive non-boolean selection count."""
        if isinstance(self.count, bool) or not isinstance(self.count, int):
            raise TypeError("count must be an int.")
        if self.count <= 0:
            raise ValueError("count must be positive.")

    def select(self, ranking: ObjectiveRanking) -> ObjectiveSelection:
        """Return up to ``count`` leading entries without filtering or reranking."""
        if not isinstance(ranking, ObjectiveRanking):
            raise TypeError("ranking must be an ObjectiveRanking.")
        return ObjectiveSelection(ranking, ranking.ranked_scores[: self.count])


def _source_position(
    selected_score: RankedObjectiveScore,
    source_scores: tuple[RankedObjectiveScore, ...],
) -> int | None:
    """Return the identity-based source position for one selected ranking entry."""
    return next(
        (
            index
            for index, source_score in enumerate(source_scores)
            if source_score is selected_score
        ),
        None,
    )
