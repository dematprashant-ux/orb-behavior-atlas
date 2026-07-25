"""Contract tests for deterministic objective ranking without selection policy."""

from dataclasses import FrozenInstanceError, is_dataclass
from unittest import TestCase

from src.engines.backtesting import (
    BacktestContext,
    BacktestRun,
    BacktestStatus,
    CandidateEvaluation,
    ObjectiveDirection,
    ObjectiveRanker,
    ObjectiveRanking,
    ObjectiveScore,
    RankedObjectiveScore,
    StandardObjectiveRanker,
)
from src.engines.execution import ExecutionRequest, ExecutionResult, ExecutionStatus
from src.engines.research import ORBBehaviorAtlas
from src.engines.strategy import CandidateParameterSet, ORBRuleStrategy


class ObjectiveRankingTests(TestCase):
    """Verify stable directional ordering without scoring or selecting candidates."""

    def test_maximize_ranks_descending_and_preserves_equal_score_input_order(self) -> None:
        first = _score("first", 3.0, ObjectiveDirection.MAXIMIZE)
        second = _score("second", 5.0, ObjectiveDirection.MAXIMIZE)
        third = _score("third", 5.0, ObjectiveDirection.MAXIMIZE)

        ranking = StandardObjectiveRanker(ObjectiveDirection.MAXIMIZE).rank(
            (first, second, third)
        )

        self.assertEqual(ranking.direction, ObjectiveDirection.MAXIMIZE)
        self.assertEqual(
            tuple(item.source_score for item in ranking.ranked_scores),
            (second, third, first),
        )
        self.assertEqual(tuple(item.rank for item in ranking.ranked_scores), (1, 2, 3))

    def test_minimize_ranks_ascending(self) -> None:
        first = _score("first", 3.0, ObjectiveDirection.MINIMIZE)
        second = _score("second", 1.0, ObjectiveDirection.MINIMIZE)

        ranking = StandardObjectiveRanker(ObjectiveDirection.MINIMIZE).rank(
            (first, second)
        )

        self.assertEqual(
            tuple(item.source_score for item in ranking.ranked_scores),
            (second, first),
        )

    def test_empty_ranking_uses_the_explicit_ranker_direction(self) -> None:
        ranking = StandardObjectiveRanker(ObjectiveDirection.MINIMIZE).rank(())

        self.assertEqual(ranking.direction, ObjectiveDirection.MINIMIZE)
        self.assertEqual(ranking.ranked_scores, ())

    def test_models_are_immutable_and_have_deterministic_value_semantics(self) -> None:
        score = _score("one", 1.0, ObjectiveDirection.MAXIMIZE)
        ranked = RankedObjectiveScore(score, 1)
        ranking = ObjectiveRanking(ObjectiveDirection.MAXIMIZE, (ranked,))

        self.assertTrue(is_dataclass(ranked))
        self.assertTrue(is_dataclass(ranking))
        self.assertFalse(hasattr(ranked, "__dict__"))
        self.assertFalse(hasattr(ranking, "__dict__"))
        self.assertEqual(ranked, RankedObjectiveScore(score, 1))
        self.assertEqual(repr(ranking), repr(ObjectiveRanking(ranking.direction, (ranked,))))
        with self.assertRaises(FrozenInstanceError):
            ranked.rank = 2  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            ranking.ranked_scores = ()  # type: ignore[misc]

    def test_models_reject_invalid_intrinsic_values(self) -> None:
        score = _score("one", 1.0, ObjectiveDirection.MAXIMIZE)
        ranked = RankedObjectiveScore(score, 1)

        with self.assertRaisesRegex(TypeError, "source_score"):
            RankedObjectiveScore(None, 1)  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "rank"):
            RankedObjectiveScore(score, True)  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "positive"):
            RankedObjectiveScore(score, 0)
        with self.assertRaisesRegex(TypeError, "direction"):
            ObjectiveRanking("maximize", ())  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "ranked_scores"):
            ObjectiveRanking(ObjectiveDirection.MAXIMIZE, [])  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "match"):
            ObjectiveRanking(ObjectiveDirection.MINIMIZE, (ranked,))
        with self.assertRaisesRegex(ValueError, "contiguous"):
            ObjectiveRanking(
                ObjectiveDirection.MAXIMIZE,
                (RankedObjectiveScore(score, 2),),
            )

    def test_ranker_protocol_and_direction_validation(self) -> None:
        ranker: ObjectiveRanker = StandardObjectiveRanker(ObjectiveDirection.MAXIMIZE)
        score = _score("one", 1.0, ObjectiveDirection.MAXIMIZE)

        self.assertEqual(ranker.rank((score,)).ranked_scores[0].source_score, score)
        with self.assertRaisesRegex(TypeError, "direction"):
            StandardObjectiveRanker("maximize")  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "scores"):
            ranker.rank([])  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "match"):
            ranker.rank((_score("two", 1.0, ObjectiveDirection.MINIMIZE),))

    def test_public_exports_are_intentional(self) -> None:
        from src.engines.backtesting import ObjectiveRanker as PackageRanker
        from src.engines.backtesting import ObjectiveRanking as PackageRanking
        from src.engines.backtesting import RankedObjectiveScore as PackageScore
        from src.engines.backtesting import StandardObjectiveRanker as PackageStandard

        self.assertIs(PackageRanker, ObjectiveRanker)
        self.assertIs(PackageRanking, ObjectiveRanking)
        self.assertIs(PackageScore, RankedObjectiveScore)
        self.assertIs(PackageStandard, StandardObjectiveRanker)


class _SkippedExecutionEngine:
    """Minimal execution dependency for structural BacktestRun construction."""

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Return a skipped result without executing a trade."""
        return ExecutionResult(request, ExecutionStatus.SKIPPED)


def _score(
    name: str,
    value: float,
    direction: ObjectiveDirection,
) -> ObjectiveScore:
    """Create one completed typed score without objective calculation behavior."""
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
