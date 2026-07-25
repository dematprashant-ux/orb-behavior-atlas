"""Contract tests for generic immutable optimization search results."""

from dataclasses import FrozenInstanceError, is_dataclass
from unittest import TestCase

from src.engines.backtesting import (
    BacktestContext,
    BacktestRun,
    BacktestStatus,
    CandidateEvaluation,
    OptimizationSearchRun,
    OptimizationStrategyMetadata,
)
from src.engines.execution import ExecutionRequest, ExecutionResult, ExecutionStatus
from src.engines.research import ORBBehaviorAtlas
from src.engines.strategy import CandidateParameterSet, ORBRuleStrategy


class OptimizationSearchRunTests(TestCase):
    """Verify generic ordered evaluations without algorithm-specific state."""

    def test_empty_run_is_immutable_and_deterministic(self) -> None:
        first = OptimizationSearchRun(_metadata())
        second = OptimizationSearchRun(_metadata())

        self.assertTrue(is_dataclass(first))
        self.assertFalse(hasattr(first, "__dict__"))
        self.assertEqual(first, second)
        self.assertEqual(repr(first), repr(second))
        with self.assertRaises(FrozenInstanceError):
            first.evaluations = ()  # type: ignore[misc]

    def test_populated_run_retains_exact_evaluation_references_in_order(self) -> None:
        first = _evaluation("first")
        second = _evaluation("second")
        metadata = _metadata()
        run = OptimizationSearchRun(metadata, (first, second))

        self.assertIs(run.strategy_metadata, metadata)
        self.assertIs(run.evaluations[0], first)
        self.assertIs(run.evaluations[1], second)

    def test_run_rejects_non_tuple_or_non_evaluation_values(self) -> None:
        with self.assertRaisesRegex(TypeError, "tuple"):
            OptimizationSearchRun(_metadata(), [])  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "only"):
            OptimizationSearchRun(_metadata(), (None,))  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "strategy_metadata"):
            OptimizationSearchRun(None)  # type: ignore[arg-type]

    def test_public_export_is_intentional(self) -> None:
        from src.engines.backtesting import OptimizationSearchRun as PackageRun

        self.assertIs(PackageRun, OptimizationSearchRun)


class _SkippedExecutionEngine:
    """Minimal dependency required to create an existing immutable backtest run."""

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Return a skipped immutable execution result without executing trades."""
        return ExecutionResult(request, ExecutionStatus.SKIPPED)


def _evaluation(name: str) -> CandidateEvaluation:
    """Create one existing candidate evaluation without search behavior."""
    context = BacktestContext(
        behavior_atlas=ORBBehaviorAtlas(records=()),
        strategy=ORBRuleStrategy(),
        execution_engine=_SkippedExecutionEngine(),
    )
    return CandidateEvaluation(
        CandidateParameterSet((("candidate", name),)),
        BacktestRun(context, BacktestStatus.COMPLETED),
    )


def _metadata() -> OptimizationStrategyMetadata:
    """Return one immutable algorithm identity for generic search-run tests."""
    return OptimizationStrategyMetadata("test")
