"""Contract tests for immutable informational optimization progress."""

from dataclasses import FrozenInstanceError, is_dataclass
from unittest import TestCase

from src.engines.backtesting import (
    BacktestContext,
    BacktestRun,
    BacktestStatus,
    DeterministicRandomCandidateSampler,
    GridOptimizationStrategy,
    OptimizationBudget,
    OptimizationConfiguration,
    OptimizationProgress,
    OptimizationSpecification,
    RandomOptimizationConfiguration,
    RandomOptimizationStrategy,
    StandardGridSearchRunner,
)
from src.engines.backtesting.evaluation import CandidateEvaluation
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


class OptimizationProgressTests(TestCase):
    """Verify deterministic progress remains informational and immutable."""

    def test_progress_is_immutable_and_has_deterministic_ratio(self) -> None:
        progress = OptimizationProgress(1, 4)

        self.assertTrue(is_dataclass(progress))
        self.assertFalse(hasattr(progress, "__dict__"))
        self.assertEqual(progress, OptimizationProgress(1, 4))
        self.assertEqual(repr(progress), repr(OptimizationProgress(1, 4)))
        self.assertEqual(progress.completion_ratio, 0.25)
        with self.assertRaises(FrozenInstanceError):
            progress.evaluated_candidates = 2  # type: ignore[misc]

    def test_progress_handles_zero_and_rejects_inconsistent_counts(self) -> None:
        self.assertEqual(OptimizationProgress(0, 0).completion_ratio, 0.0)
        with self.assertRaisesRegex(ValueError, "exceed"):
            OptimizationProgress(2, 1)
        with self.assertRaisesRegex(TypeError, "evaluated_candidates"):
            OptimizationProgress(True, 1)  # type: ignore[arg-type]

    def test_grid_and_random_search_runs_report_budgeted_progress(self) -> None:
        grid_space = _grid_space()
        grid_result = GridOptimizationStrategy(
            StandardGridSearchRunner(GridCandidateGenerator(), _Evaluator())
        ).execute(_specification(grid_space, OptimizationBudget(1)))
        self.assertEqual(grid_result.progress, OptimizationProgress(1, 3))

        random_space = _random_space()
        random_result = RandomOptimizationStrategy(
            DeterministicRandomCandidateSampler(CartesianParameterSpaceIndexer()),
            _Evaluator(),
            RandomOptimizationConfiguration(17, 4),
        ).execute(_specification(random_space, OptimizationBudget(2)))
        self.assertEqual(random_result.progress, OptimizationProgress(2, 6))

    def test_progress_public_export_is_intentional(self) -> None:
        from src.engines.backtesting import OptimizationProgress as PackageProgress

        self.assertIs(PackageProgress, OptimizationProgress)


class _SelectionPolicy:
    """Minimal policy only for immutable specification construction."""

    def select(self, ranking: ObjectiveRanking) -> ObjectiveSelection:
        """Return an empty selection retaining the exact supplied ranking."""
        return ObjectiveSelection(ranking)


class _Evaluator:
    """Test-only evaluator returning one existing immutable outcome per candidate."""

    def __init__(self) -> None:
        self.outcome = _outcome()

    def evaluate(self, candidate: CandidateParameterSet) -> CandidateEvaluation:
        """Return one typed evaluation without scoring or execution behavior."""
        return CandidateEvaluation(candidate, self.outcome)


class _SkippedExecutionEngine:
    """Minimal execution dependency for structural immutable backtest results."""

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Return a skipped result without executing a trade."""
        return ExecutionResult(request, ExecutionStatus.SKIPPED)


def _grid_space() -> ParameterSpace:
    """Return a three-candidate ordered grid space."""
    return ParameterSpace((DiscreteParameter("orb_minutes", (5, 15, 30)),))


def _random_space() -> ParameterSpace:
    """Return a six-candidate ordered random-sampling space."""
    return ParameterSpace(
        (
            DiscreteParameter("orb_minutes", (5, 15, 30)),
            DiscreteParameter("target_multiple", (1.0, 2.0)),
        )
    )


def _specification(
    parameter_space: ParameterSpace,
    budget: OptimizationBudget,
) -> OptimizationSpecification:
    """Build one explicit optimization input with no execution collaborators."""
    return OptimizationSpecification(
        parameter_space,
        OptimizationConfiguration(ObjectiveDirection.MAXIMIZE, _SelectionPolicy()),
        budget,
    )


def _outcome() -> BacktestRun:
    """Create one existing immutable outcome without a real backtest."""
    context = BacktestContext(
        behavior_atlas=ORBBehaviorAtlas(records=()),
        strategy=ORBRuleStrategy(),
        execution_engine=_SkippedExecutionEngine(),
    )
    return BacktestRun(context, BacktestStatus.COMPLETED)
