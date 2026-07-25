"""Contract tests for typed candidate evaluation without optimizer behavior."""

from dataclasses import FrozenInstanceError, is_dataclass
from unittest import TestCase

from src.engines.backtesting import (
    BacktestContext,
    BacktestRun,
    BacktestStatus,
    CandidateEvaluation,
    CandidateEvaluator,
)
from src.engines.execution import ExecutionRequest, ExecutionResult, ExecutionStatus
from src.engines.research import ORBBehaviorAtlas
from src.engines.strategy import CandidateParameterSet, ORBRuleStrategy


class CandidateEvaluationContractTests(TestCase):
    """Verify candidate evaluation is an immutable protocol-only hand-off."""

    def test_evaluation_is_immutable_and_retains_existing_references(self) -> None:
        candidate = CandidateParameterSet((("orb_minutes", 15),))
        outcome = _outcome()

        evaluation = CandidateEvaluation(candidate, outcome)

        self.assertTrue(is_dataclass(evaluation))
        self.assertFalse(hasattr(evaluation, "__dict__"))
        self.assertIs(evaluation.candidate, candidate)
        self.assertIs(evaluation.outcome, outcome)
        self.assertEqual(evaluation, CandidateEvaluation(candidate, outcome))
        self.assertEqual(repr(evaluation), repr(CandidateEvaluation(candidate, outcome)))
        with self.assertRaises(FrozenInstanceError):
            evaluation.candidate = CandidateParameterSet(())  # type: ignore[misc]

    def test_evaluation_rejects_intrinsic_type_misuse(self) -> None:
        with self.assertRaisesRegex(TypeError, "candidate"):
            CandidateEvaluation(None, _outcome())  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "outcome"):
            CandidateEvaluation(CandidateParameterSet(()), None)  # type: ignore[arg-type]

    def test_evaluator_protocol_supports_a_deterministic_injected_implementation(
        self,
    ) -> None:
        candidate = CandidateParameterSet((("orb_minutes", 15),))
        evaluator: CandidateEvaluator = _Evaluator()

        evaluation = evaluator.evaluate(candidate)

        self.assertIs(evaluation.candidate, candidate)
        self.assertEqual(evaluation.outcome.status, BacktestStatus.COMPLETED)

    def test_public_exports_retain_the_existing_backtest_result_model(self) -> None:
        from src.engines.backtesting import CandidateEvaluation as PackageEvaluation
        from src.engines.backtesting import CandidateEvaluator as PackageEvaluator

        self.assertIs(PackageEvaluation, CandidateEvaluation)
        self.assertIs(PackageEvaluator, CandidateEvaluator)


class _Evaluator:
    """Minimal deterministic evaluator test double without optimization logic."""

    def evaluate(self, candidate: CandidateParameterSet) -> CandidateEvaluation:
        """Return the existing fixed backtest outcome for one candidate."""
        return CandidateEvaluation(candidate, _outcome())


class _SkippedExecutionEngine:
    """Minimal execution dependency for structural BacktestRun construction."""

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Return a skipped result without executing a trade."""
        return ExecutionResult(request, ExecutionStatus.SKIPPED)


def _outcome() -> BacktestRun:
    """Construct one complete existing backtest result without evaluation work."""
    context = BacktestContext(
        behavior_atlas=ORBBehaviorAtlas(records=()),
        strategy=ORBRuleStrategy(),
        execution_engine=_SkippedExecutionEngine(),
    )
    return BacktestRun(context, BacktestStatus.COMPLETED)
