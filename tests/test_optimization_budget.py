"""Contract tests for immutable deterministic optimization evaluation budgets."""

from dataclasses import FrozenInstanceError, dataclass, is_dataclass
from unittest import TestCase

from src.engines.backtesting import (
    BacktestContext,
    BacktestRun,
    BacktestStatus,
    DeterministicRandomCandidateSampler,
    GridOptimizationStrategy,
    OptimizationBudget,
    OptimizationConfiguration,
    OptimizationSpecification,
    RandomOptimizationConfiguration,
    RandomOptimizationStrategy,
    StandardGridSearchRunner,
)
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
from src.engines.backtesting.objectives import ObjectiveDirection
from src.engines.backtesting.evaluation import CandidateEvaluation
from src.engines.backtesting.ranking import ObjectiveRanking
from src.engines.backtesting.selection import ObjectiveSelection


class OptimizationBudgetTests(TestCase):
    """Verify deterministic limits remain separate from optimization policy."""

    def test_budget_is_immutable_and_has_deterministic_value_semantics(self) -> None:
        budget = OptimizationBudget(2)

        self.assertTrue(is_dataclass(budget))
        self.assertFalse(hasattr(budget, "__dict__"))
        self.assertEqual(budget, OptimizationBudget(2))
        self.assertEqual(repr(budget), repr(OptimizationBudget(2)))
        with self.assertRaises(FrozenInstanceError):
            budget.maximum_evaluations = 1  # type: ignore[misc]

    def test_budget_rejects_invalid_values_and_is_exported(self) -> None:
        for value in (True, 1.0, "1"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(TypeError, "maximum_evaluations"):
                    OptimizationBudget(value)  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "negative"):
            OptimizationBudget(-1)

        from src.engines.backtesting import OptimizationBudget as PackageBudget

        self.assertIs(PackageBudget, OptimizationBudget)

    def test_grid_strategy_truncates_evaluation_in_canonical_order(self) -> None:
        parameter_space = _parameter_space()
        evaluator = _RecordingEvaluator()
        strategy = GridOptimizationStrategy(
            StandardGridSearchRunner(GridCandidateGenerator(), evaluator)
        )

        result = strategy.execute(
            _specification(parameter_space, OptimizationBudget(1))
        )

        self.assertEqual(
            tuple(
                evaluation.candidate.assignments
                for evaluation in result.evaluations
            ),
            ((("orb_minutes", 5),),),
        )
        self.assertEqual(
            evaluator.candidates,
            [CandidateParameterSet((("orb_minutes", 5),))],
        )

    def test_grid_strategy_evaluates_all_when_budget_meets_or_exceeds_space(
        self,
    ) -> None:
        parameter_space = _parameter_space()

        equal_result = GridOptimizationStrategy(
            StandardGridSearchRunner(GridCandidateGenerator(), _RecordingEvaluator())
        ).execute(_specification(parameter_space, OptimizationBudget(3)))
        larger_result = GridOptimizationStrategy(
            StandardGridSearchRunner(GridCandidateGenerator(), _RecordingEvaluator())
        ).execute(_specification(parameter_space, OptimizationBudget(10)))

        self.assertEqual(len(equal_result.evaluations), 3)
        self.assertEqual(
            tuple(item.candidate for item in equal_result.evaluations),
            tuple(item.candidate for item in larger_result.evaluations),
        )

    def test_random_strategy_truncates_evaluation_without_changing_sample_order(
        self,
    ) -> None:
        parameter_space = ParameterSpace(
            (
                DiscreteParameter("orb_minutes", (5, 15, 30)),
                DiscreteParameter("target_multiple", (1.0, 2.0)),
            )
        )
        evaluator = _RecordingEvaluator()
        strategy = RandomOptimizationStrategy(
            DeterministicRandomCandidateSampler(CartesianParameterSpaceIndexer()),
            evaluator,
            RandomOptimizationConfiguration(17, 4),
        )

        result = strategy.execute(
            _specification(parameter_space, OptimizationBudget(2))
        )

        self.assertEqual(
            tuple(item.candidate.assignments for item in result.evaluations),
            (
                (("orb_minutes", 30), ("target_multiple", 1.0)),
                (("orb_minutes", 15), ("target_multiple", 2.0)),
            ),
        )
        self.assertEqual(len(evaluator.candidates), 2)


@dataclass(frozen=True, slots=True)
class _SelectionPolicy:
    """Minimal structural policy needed to build optimization specifications."""

    def select(self, ranking: ObjectiveRanking) -> ObjectiveSelection:
        """Retain the source ranking without adding selection behavior."""
        return ObjectiveSelection(ranking)


class _RecordingEvaluator:
    """Test-only evaluator retaining each candidate in deterministic order."""

    def __init__(self) -> None:
        self.candidates: list[CandidateParameterSet] = []
        self.outcome = _outcome()

    def evaluate(self, candidate: CandidateParameterSet) -> CandidateEvaluation:
        """Record a candidate and return one immutable existing evaluation."""
        self.candidates.append(candidate)
        return CandidateEvaluation(candidate, self.outcome)


class _SkippedExecutionEngine:
    """Minimal execution dependency needed for a structural BacktestRun."""

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Return a skipped result without trade execution behavior."""
        return ExecutionResult(request, ExecutionStatus.SKIPPED)


def _parameter_space() -> ParameterSpace:
    """Return a three-candidate ordered space for grid truncation coverage."""
    return ParameterSpace((DiscreteParameter("orb_minutes", (5, 15, 30)),))


def _specification(
    parameter_space: ParameterSpace,
    budget: OptimizationBudget,
) -> OptimizationSpecification:
    """Return an explicit immutable specification with one evaluation budget."""
    return OptimizationSpecification(
        parameter_space,
        OptimizationConfiguration(ObjectiveDirection.MAXIMIZE, _SelectionPolicy()),
        budget,
    )


def _outcome() -> BacktestRun:
    """Return one existing immutable result without performing a backtest."""
    context = BacktestContext(
        behavior_atlas=ORBBehaviorAtlas(records=()),
        strategy=ORBRuleStrategy(),
        execution_engine=_SkippedExecutionEngine(),
    )
    return BacktestRun(context, BacktestStatus.COMPLETED)
