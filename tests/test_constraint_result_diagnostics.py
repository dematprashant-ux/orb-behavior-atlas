"""Contract tests for retained rejected-candidate optimization diagnostics."""

from dataclasses import FrozenInstanceError
from unittest import TestCase

from src.engines.backtesting import (
    BacktestContext,
    BacktestRun,
    BacktestStatus,
    CandidateEvaluation,
    ConstraintDiagnostic,
    ConstraintEvaluationResult,
    ConstraintDiagnostics,
    ConstraintRejection,
    DeterministicRandomCandidateSampler,
    GridOptimizationStrategy,
    OptimizationBudget,
    OptimizationConfiguration,
    OptimizationSpecification,
    RandomOptimizationConfiguration,
    RandomOptimizationStrategy,
    StandardGridSearchRunner,
)
from src.engines.backtesting.objectives import ObjectiveDirection
from src.engines.backtesting.ranking import ObjectiveRanking
from src.engines.backtesting.selection import ObjectiveSelection
from src.engines.execution import ExecutionRequest, ExecutionResult, ExecutionStatus
from src.engines.research import ORBBehaviorAtlas
from src.engines.strategy import (
    CandidateParameterSet,
    CartesianParameterSpaceIndexer,
    DiscreteParameter,
    GridCandidateGenerator,
    ORBRuleStrategy,
    ParameterSpace,
)
from src.engines.backtesting.constraints import OptimizationConstraints


class ConstraintResultDiagnosticsTests(TestCase):
    """Verify rejected-candidate details remain informational and immutable."""

    def test_rejection_models_retain_exact_references_immutably(self) -> None:
        candidate = CandidateParameterSet((("orb_minutes", 15),))
        diagnostic = ConstraintDiagnostic("minimum_orb", "too_short")
        rejection = ConstraintRejection(candidate, diagnostic)
        diagnostics = ConstraintDiagnostics((rejection,))

        self.assertIs(rejection.candidate, candidate)
        self.assertIs(rejection.diagnostic, diagnostic)
        self.assertIs(diagnostics.rejections[0], rejection)
        self.assertEqual(diagnostics, ConstraintDiagnostics((rejection,)))
        self.assertEqual(repr(diagnostics), repr(ConstraintDiagnostics((rejection,))))
        with self.assertRaises(FrozenInstanceError):
            rejection.candidate = candidate  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            diagnostics.rejections = ()  # type: ignore[misc]

    def test_grid_records_rejections_once_without_evaluating_them(self) -> None:
        first, rejected, third = _candidates()
        constraint = _RecordingConstraint({rejected})
        evaluator = _RecordingEvaluator()
        specification = _specification(
            _space(),
            OptimizationBudget(2),
            OptimizationConstraints((constraint,)),
        )

        result = GridOptimizationStrategy(
            StandardGridSearchRunner(GridCandidateGenerator(), evaluator)
        ).execute(specification)

        self.assertEqual(constraint.candidates, [first, rejected, third])
        self.assertEqual(evaluator.candidates, [first, third])
        self.assertEqual(result.progress.evaluated_candidates, 2)
        self.assertEqual(result.progress.total_candidates, 2)
        self.assertEqual(
            tuple(item.candidate for item in result.constraint_diagnostics.rejections),
            (rejected,),
        )
        self.assertIs(
            result.constraint_diagnostics.rejections[0].diagnostic,
            constraint.diagnostics[0],
        )

    def test_random_records_sample_order_and_retains_identity(self) -> None:
        first, rejected, third = _candidates()
        constraint = _RecordingConstraint({rejected})
        evaluator = _RecordingEvaluator()
        strategy = RandomOptimizationStrategy(
            _Sampler((third, rejected, first)),
            evaluator,
            RandomOptimizationConfiguration(7, 3),
        )
        result = strategy.execute(
            _specification(
                _space(),
                OptimizationBudget(2),
                OptimizationConstraints((constraint,)),
            )
        )

        self.assertEqual(constraint.candidates, [third, rejected, first])
        self.assertEqual(evaluator.candidates, [third, first])
        self.assertEqual(
            tuple(item.candidate for item in result.constraint_diagnostics.rejections),
            (rejected,),
        )
        self.assertEqual(result.progress.evaluated_candidates, 2)
        self.assertEqual(result.progress.total_candidates, 2)

    def test_public_exports_are_intentional(self) -> None:
        from src.engines.backtesting import (
            ConstraintDiagnostics as PackageDiagnostics,
        )
        from src.engines.backtesting import ConstraintRejection as PackageRejection

        self.assertIs(PackageDiagnostics, ConstraintDiagnostics)
        self.assertIs(PackageRejection, ConstraintRejection)


class _RecordingConstraint:
    """Test-only diagnostic authority that records one traversal per candidate."""

    def __init__(self, rejected: set[CandidateParameterSet]) -> None:
        self.rejected = rejected
        self.candidates: list[CandidateParameterSet] = []
        self.diagnostics: list[ConstraintDiagnostic] = []

    def evaluate(self, candidate: CandidateParameterSet) -> ConstraintEvaluationResult:
        """Record one authoritative constraint result for the exact candidate."""
        self.candidates.append(candidate)
        if candidate not in self.rejected:
            return ConstraintEvaluationResult(True, None)
        diagnostic = ConstraintDiagnostic("test_constraint", "rejected")
        self.diagnostics.append(diagnostic)
        return ConstraintEvaluationResult(False, diagnostic)


class _RecordingEvaluator:
    """Test-only evaluator retaining eligible candidates in evaluation order."""

    def __init__(self) -> None:
        self.candidates: list[CandidateParameterSet] = []
        self.outcome = _outcome()

    def evaluate(self, candidate: CandidateParameterSet) -> CandidateEvaluation:
        """Record and return an immutable evaluation for one eligible candidate."""
        self.candidates.append(candidate)
        return CandidateEvaluation(candidate, self.outcome)


class _Sampler:
    """Test-only deterministic sampler returning its supplied immutable order."""

    def __init__(self, candidates: tuple[CandidateParameterSet, ...]) -> None:
        self.candidates = candidates

    def sample(
        self,
        parameter_space: ParameterSpace,
        configuration: RandomOptimizationConfiguration,
    ) -> tuple[CandidateParameterSet, ...]:
        """Return the supplied sequence without generating or mutating candidates."""
        del parameter_space, configuration
        return self.candidates


class _SelectionPolicy:
    """Minimal immutable selection collaborator for specification construction."""

    def select(self, ranking: ObjectiveRanking) -> ObjectiveSelection:
        """Retain the supplied ranking without selecting a production winner."""
        return ObjectiveSelection(ranking)


class _SkippedExecutionEngine:
    """Minimal execution dependency for immutable structural test outcomes."""

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Return a skipped result without execution behavior."""
        return ExecutionResult(request, ExecutionStatus.SKIPPED)


def _space() -> ParameterSpace:
    """Return the ordered three-candidate space used by both strategy tests."""
    return ParameterSpace((DiscreteParameter("orb_minutes", (5, 15, 30)),))


def _candidates() -> tuple[CandidateParameterSet, ...]:
    """Return canonical grid-order candidate values for the finite test space."""
    return tuple(
        CandidateParameterSet((("orb_minutes", value),))
        for value in (5, 15, 30)
    )


def _specification(
    parameter_space: ParameterSpace,
    budget: OptimizationBudget,
    constraints: OptimizationConstraints,
) -> OptimizationSpecification:
    """Return one explicit immutable optimization specification for testing."""
    return OptimizationSpecification(
        parameter_space,
        OptimizationConfiguration(ObjectiveDirection.MAXIMIZE, _SelectionPolicy()),
        budget,
        constraints,
    )


def _outcome() -> BacktestRun:
    """Return one existing immutable completed result without a backtest run."""
    context = BacktestContext(
        behavior_atlas=ORBBehaviorAtlas(records=()),
        strategy=ORBRuleStrategy(),
        execution_engine=_SkippedExecutionEngine(),
    )
    return BacktestRun(context, BacktestStatus.COMPLETED)
