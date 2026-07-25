"""Contract tests for typed candidate objectives without selection behavior."""

from dataclasses import FrozenInstanceError, is_dataclass
from math import inf, nan
from unittest import TestCase

from src.engines.backtesting import (
    BacktestContext,
    BacktestRun,
    BacktestStatus,
    CandidateEvaluation,
    CandidateObjective,
    ObjectiveDirection,
    ObjectiveScore,
)
from src.engines.execution import ExecutionRequest, ExecutionResult, ExecutionStatus
from src.engines.research import ORBBehaviorAtlas
from src.engines.strategy import CandidateParameterSet, ORBRuleStrategy


class CandidateObjectiveContractTests(TestCase):
    """Verify immutable directional scores without ranking or concrete formulas."""

    def test_score_is_immutable_deterministic_and_retains_its_evaluation(self) -> None:
        evaluation = _evaluation()
        score = ObjectiveScore(evaluation, 12.5, ObjectiveDirection.MAXIMIZE)

        self.assertTrue(is_dataclass(score))
        self.assertFalse(hasattr(score, "__dict__"))
        self.assertIs(score.evaluation, evaluation)
        self.assertEqual(score, ObjectiveScore(evaluation, 12.5, ObjectiveDirection.MAXIMIZE))
        self.assertEqual(
            repr(score),
            repr(ObjectiveScore(evaluation, 12.5, ObjectiveDirection.MAXIMIZE)),
        )
        with self.assertRaises(FrozenInstanceError):
            score.score = 0.0  # type: ignore[misc]

    def test_direction_values_are_stable_and_explicit(self) -> None:
        self.assertEqual(ObjectiveDirection.MAXIMIZE.value, "maximize")
        self.assertEqual(ObjectiveDirection.MINIMIZE.value, "minimize")

    def test_score_accepts_finite_int_and_float_inputs_as_canonical_floats(self) -> None:
        evaluation = _evaluation()

        integer_score = ObjectiveScore(evaluation, 12, ObjectiveDirection.MAXIMIZE)
        float_score = ObjectiveScore(evaluation, 12.5, ObjectiveDirection.MINIMIZE)

        self.assertEqual(integer_score.score, 12.0)
        self.assertIsInstance(integer_score.score, float)
        self.assertEqual(float_score.score, 12.5)

    def test_score_rejects_invalid_intrinsic_values(self) -> None:
        evaluation = _evaluation()

        with self.assertRaisesRegex(TypeError, "evaluation"):
            ObjectiveScore(None, 1.0, ObjectiveDirection.MAXIMIZE)  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "score"):
            ObjectiveScore(evaluation, True, ObjectiveDirection.MAXIMIZE)  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "finite"):
            ObjectiveScore(evaluation, nan, ObjectiveDirection.MAXIMIZE)
        with self.assertRaisesRegex(ValueError, "finite"):
            ObjectiveScore(evaluation, inf, ObjectiveDirection.MAXIMIZE)
        with self.assertRaisesRegex(ValueError, "finite"):
            ObjectiveScore(evaluation, -inf, ObjectiveDirection.MAXIMIZE)
        with self.assertRaisesRegex(ValueError, "finite"):
            ObjectiveScore(evaluation, 10**400, ObjectiveDirection.MAXIMIZE)
        with self.assertRaisesRegex(TypeError, "direction"):
            ObjectiveScore(evaluation, 1.0, "maximize")  # type: ignore[arg-type]

    def test_objective_protocol_supports_a_deterministic_injected_implementation(
        self,
    ) -> None:
        objective: CandidateObjective = _FixedObjective()
        evaluation = _evaluation()

        score = objective.score(evaluation)

        self.assertIs(score.evaluation, evaluation)
        self.assertEqual(score.score, 0.0)
        self.assertIs(score.direction, ObjectiveDirection.MINIMIZE)

    def test_public_exports_are_intentional(self) -> None:
        from src.engines.backtesting import CandidateObjective as PackageObjective
        from src.engines.backtesting import ObjectiveDirection as PackageDirection
        from src.engines.backtesting import ObjectiveScore as PackageScore

        self.assertIs(PackageObjective, CandidateObjective)
        self.assertIs(PackageDirection, ObjectiveDirection)
        self.assertIs(PackageScore, ObjectiveScore)


class _FixedObjective:
    """Minimal protocol test double with no formula or selection behavior."""

    def score(self, evaluation: CandidateEvaluation) -> ObjectiveScore:
        """Return a fixed valid score for one existing immutable evaluation."""
        return ObjectiveScore(evaluation, 0.0, ObjectiveDirection.MINIMIZE)


class _SkippedExecutionEngine:
    """Minimal execution dependency for structural BacktestRun construction."""

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Return a skipped result without executing a trade."""
        return ExecutionResult(request, ExecutionStatus.SKIPPED)


def _evaluation() -> CandidateEvaluation:
    """Create one candidate evaluation without scoring or performance calculation."""
    context = BacktestContext(
        behavior_atlas=ORBBehaviorAtlas(records=()),
        strategy=ORBRuleStrategy(),
        execution_engine=_SkippedExecutionEngine(),
    )
    outcome = BacktestRun(context, BacktestStatus.COMPLETED)
    return CandidateEvaluation(CandidateParameterSet((("orb_minutes", 15),)), outcome)
