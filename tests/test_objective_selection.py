"""Contract tests for deterministic selection from completed objective rankings."""

from dataclasses import FrozenInstanceError, is_dataclass
from unittest import TestCase

from src.engines.backtesting import (
    BacktestContext,
    BacktestRun,
    BacktestStatus,
    BestRankSelectionPolicy,
    CandidateEvaluation,
    ObjectiveDirection,
    ObjectiveRanking,
    ObjectiveScore,
    ObjectiveSelection,
    RankedObjectiveScore,
    SelectionPolicy,
    TopRankedSelectionPolicy,
)
from src.engines.execution import ExecutionRequest, ExecutionResult, ExecutionStatus
from src.engines.research import ORBBehaviorAtlas
from src.engines.strategy import CandidateParameterSet, ORBRuleStrategy


class ObjectiveSelectionTests(TestCase):
    """Verify source-ordered selection without score or ranking behavior."""

    def test_best_policy_selects_all_leading_score_ties_and_empty_rankings_stay_empty(
        self,
    ) -> None:
        ranking = _ranking()

        selection = BestRankSelectionPolicy().select(ranking)
        empty = BestRankSelectionPolicy().select(
            ObjectiveRanking(ObjectiveDirection.MAXIMIZE)
        )

        self.assertIs(selection.ranking, ranking)
        self.assertEqual(selection.selected_scores, ranking.ranked_scores[:2])
        self.assertEqual(empty.selected_scores, ())

    def test_top_ranked_policy_preserves_order_and_limits_to_the_requested_count(
        self,
    ) -> None:
        ranking = _ranking()
        policy: SelectionPolicy = TopRankedSelectionPolicy(2)

        selection = policy.select(ranking)
        cutoff = TopRankedSelectionPolicy(1).select(ranking)
        complete = TopRankedSelectionPolicy(10).select(ranking)

        self.assertEqual(selection.selected_scores, ranking.ranked_scores[:2])
        self.assertEqual(cutoff.selected_scores, ranking.ranked_scores[:1])
        self.assertEqual(complete.selected_scores, ranking.ranked_scores)

    def test_selection_is_immutable_deterministic_and_retains_source_entries(
        self,
    ) -> None:
        ranking = _ranking()
        selection = ObjectiveSelection(ranking, ranking.ranked_scores[1:])

        self.assertTrue(is_dataclass(selection))
        self.assertFalse(hasattr(selection, "__dict__"))
        self.assertEqual(
            selection,
            ObjectiveSelection(ranking, ranking.ranked_scores[1:]),
        )
        self.assertEqual(
            repr(selection),
            repr(ObjectiveSelection(ranking, ranking.ranked_scores[1:])),
        )
        self.assertIs(selection.selected_scores[0], ranking.ranked_scores[1])
        with self.assertRaises(FrozenInstanceError):
            selection.selected_scores = ()  # type: ignore[misc]

    def test_selection_and_policy_models_reject_invalid_intrinsic_values(self) -> None:
        ranking = _ranking()
        first, second = ranking.ranked_scores[:2]
        foreign = RankedObjectiveScore(
            _score("foreign", 0.0, ObjectiveDirection.MAXIMIZE),
            1,
        )

        with self.assertRaisesRegex(TypeError, "ranking"):
            ObjectiveSelection(None)  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "selected_scores"):
            ObjectiveSelection(ranking, [])  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "source"):
            ObjectiveSelection(ranking, (foreign,))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            ObjectiveSelection(ranking, (first, first))
        with self.assertRaisesRegex(ValueError, "order"):
            ObjectiveSelection(ranking, (second, first))
        with self.assertRaisesRegex(TypeError, "count"):
            TopRankedSelectionPolicy(True)  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "positive"):
            TopRankedSelectionPolicy(0)
        with self.assertRaisesRegex(ValueError, "positive"):
            TopRankedSelectionPolicy(-1)
        with self.assertRaisesRegex(TypeError, "ranking"):
            BestRankSelectionPolicy().select(None)  # type: ignore[arg-type]

    def test_public_exports_are_intentional(self) -> None:
        from src.engines.backtesting import BestRankSelectionPolicy as PackageBest
        from src.engines.backtesting import ObjectiveSelection as PackageSelection
        from src.engines.backtesting import SelectionPolicy as PackagePolicy
        from src.engines.backtesting import TopRankedSelectionPolicy as PackageTop

        self.assertIs(PackageBest, BestRankSelectionPolicy)
        self.assertIs(PackageSelection, ObjectiveSelection)
        self.assertIs(PackagePolicy, SelectionPolicy)
        self.assertIs(PackageTop, TopRankedSelectionPolicy)


class _SkippedExecutionEngine:
    """Minimal execution dependency for structural BacktestRun construction."""

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Return a skipped result without executing a trade."""
        return ExecutionResult(request, ExecutionStatus.SKIPPED)


def _ranking() -> ObjectiveRanking:
    """Return one immutable source ranking in completed positional order."""
    scores = (
        _score("first", 3.0, ObjectiveDirection.MAXIMIZE),
        _score("second", 3.0, ObjectiveDirection.MAXIMIZE),
        _score("third", 1.0, ObjectiveDirection.MAXIMIZE),
    )
    return ObjectiveRanking(
        ObjectiveDirection.MAXIMIZE,
        tuple(
            RankedObjectiveScore(score, rank)
            for rank, score in enumerate(scores, start=1)
        ),
    )


def _score(
    name: str,
    value: float,
    direction: ObjectiveDirection,
) -> ObjectiveScore:
    """Create one typed score without running scoring or selection logic."""
    context = BacktestContext(
        behavior_atlas=ORBBehaviorAtlas(records=()),
        strategy=ORBRuleStrategy(),
        execution_engine=_SkippedExecutionEngine(),
    )
    evaluation = CandidateEvaluation(
        CandidateParameterSet((("candidate", name),)),
        BacktestRun(context, BacktestStatus.COMPLETED),
    )
    return ObjectiveScore(evaluation, value, direction)
