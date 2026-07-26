"""Tests for explicit immutable completed-optimization identities."""

from dataclasses import FrozenInstanceError
from unittest import TestCase

from src.engines.backtesting import (
    BacktestContext,
    BacktestRun,
    BacktestStatus,
    CandidateEvaluation,
    ConstraintDiagnostics,
    IdentifiedOptimizationRun,
    ObjectiveDirection,
    ObjectiveRanking,
    ObjectiveScore,
    ObjectiveSelection,
    OptimizationProgress,
    OptimizationRun,
    OptimizationRunIdentity,
    OptimizationSearchRun,
    OptimizationStrategyMetadata,
    OptimizationTerminationReason,
    RankedObjectiveScore,
)
from src.engines.execution import ExecutionRequest, ExecutionResult, ExecutionStatus
from src.engines.research import ORBBehaviorAtlas
from src.engines.strategy import CandidateParameterSet, ORBRuleStrategy


class OptimizationRunIdentityTests(TestCase):
    """Verify caller-owned identity is separate from completed execution results."""

    def test_identity_is_immutable_hashable_and_preserves_exact_value(self) -> None:
        identity = OptimizationRunIdentity("  run-001  ")
        equivalent = OptimizationRunIdentity("  run-001  ")

        self.assertEqual(identity.value, "  run-001  ")
        self.assertEqual(identity, equivalent)
        self.assertEqual(hash(identity), hash(equivalent))
        self.assertEqual(repr(identity), repr(equivalent))
        with self.assertRaises(FrozenInstanceError):
            identity.value = "run-002"  # type: ignore[misc]

    def test_identity_rejects_non_string_and_blank_values(self) -> None:
        for value in (None, 1, 1.0):
            with self.subTest(value=value):
                with self.assertRaisesRegex(TypeError, "value"):
                    OptimizationRunIdentity(value)  # type: ignore[arg-type]
        for value in ("", "   ", "\t"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "blank"):
                    OptimizationRunIdentity(value)

    def test_association_preserves_exact_identity_and_run_references(self) -> None:
        identity = OptimizationRunIdentity("run-001")
        run = _run()
        association = IdentifiedOptimizationRun(identity, run)

        self.assertIs(association.identity, identity)
        self.assertIs(association.run, run)
        self.assertEqual(association, IdentifiedOptimizationRun(identity, run))
        self.assertEqual(
            repr(association),
            repr(IdentifiedOptimizationRun(identity, run)),
        )
        with self.assertRaises(FrozenInstanceError):
            association.identity = OptimizationRunIdentity(
                "run-002"
            )  # type: ignore[misc]

    def test_association_requires_explicit_typed_identity_and_run(self) -> None:
        identity = OptimizationRunIdentity("run-001")
        run = _run()

        with self.assertRaisesRegex(TypeError, "identity"):
            IdentifiedOptimizationRun("run-001", run)  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "run"):
            IdentifiedOptimizationRun(identity, None)  # type: ignore[arg-type]

    def test_package_exports_are_intentional(self) -> None:
        from src.engines.backtesting import (
            IdentifiedOptimizationRun as PackageAssociation,
        )
        from src.engines.backtesting import OptimizationRunIdentity as PackageIdentity
        from src.engines.backtesting.identity import (
            IdentifiedOptimizationRun as ModuleAssociation,
        )
        from src.engines.backtesting.identity import (
            OptimizationRunIdentity as ModuleIdentity,
        )

        self.assertIs(PackageIdentity, OptimizationRunIdentity)
        self.assertIs(PackageAssociation, IdentifiedOptimizationRun)
        self.assertIs(ModuleIdentity, OptimizationRunIdentity)
        self.assertIs(ModuleAssociation, IdentifiedOptimizationRun)


class _SkippedExecutionEngine:
    """Provide the smallest execution dependency for a completed test run."""

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Return a skipped immutable result without simulating any execution."""
        return ExecutionResult(request, ExecutionStatus.SKIPPED)


def _run() -> OptimizationRun:
    """Construct a completed run without invoking optimization orchestration."""
    context = BacktestContext(
        ORBBehaviorAtlas(records=()),
        ORBRuleStrategy(),
        _SkippedExecutionEngine(),
    )
    evaluation = CandidateEvaluation(
        CandidateParameterSet((("orb_minutes", 15),)),
        BacktestRun(context, BacktestStatus.COMPLETED),
    )
    score = ObjectiveScore(evaluation, 3.0, ObjectiveDirection.MAXIMIZE)
    ranking = ObjectiveRanking(
        ObjectiveDirection.MAXIMIZE,
        (RankedObjectiveScore(score, 1),),
    )
    selection = ObjectiveSelection(ranking, ranking.ranked_scores)
    search_run = OptimizationSearchRun(
        OptimizationStrategyMetadata("test"),
        (evaluation,),
        OptimizationProgress(1, 1),
        OptimizationTerminationReason.SEARCH_SPACE_EXHAUSTED,
        ConstraintDiagnostics(),
    )
    return OptimizationRun(search_run, (score,), ranking, selection)
