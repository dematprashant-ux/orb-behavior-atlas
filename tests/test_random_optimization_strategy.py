"""Contract tests for deterministic finite random-search optimization."""

from unittest import TestCase

from src.engines.backtesting import (
    BacktestContext,
    BacktestRun,
    BacktestStatus,
    CandidateEvaluation,
    DeterministicRandomCandidateSampler,
    ObjectiveDirection,
    ObjectiveRanking,
    ObjectiveScore,
    ObjectiveSelection,
    OptimizationConfiguration,
    OptimizationSpecification,
    RandomOptimizationConfiguration,
    RandomOptimizationStrategy,
    StandardObjectiveRanker,
    StandardOptimizationRunner,
)
from src.engines.execution import ExecutionRequest, ExecutionResult, ExecutionStatus
from src.engines.research import ORBBehaviorAtlas
from src.engines.strategy import (
    CartesianParameterSpaceIndexer,
    CandidateParameterSet,
    DiscreteParameter,
    ORBRuleStrategy,
    ParameterSpace,
)


class RandomOptimizationStrategyTests(TestCase):
    """Verify reproducible unique sampling without optimization pipeline behavior."""

    def test_identical_seed_produces_identical_sampled_candidates(self) -> None:
        specification = _specification()
        first = RandomOptimizationStrategy(
            _sampler(),
            _RecordingEvaluator(),
            RandomOptimizationConfiguration(17, 4),
        ).execute(specification)
        second = RandomOptimizationStrategy(
            _sampler(),
            _RecordingEvaluator(),
            RandomOptimizationConfiguration(17, 4),
        ).execute(specification)

        self.assertEqual(
            tuple(item.candidate for item in first.evaluations),
            tuple(item.candidate for item in second.evaluations),
        )

    def test_different_seed_samples_unique_candidates_within_the_limit(self) -> None:
        specification = _specification()
        first = RandomOptimizationStrategy(
            _sampler(),
            _RecordingEvaluator(),
            RandomOptimizationConfiguration(1, 4),
        ).execute(specification)
        second = RandomOptimizationStrategy(
            _sampler(),
            _RecordingEvaluator(),
            RandomOptimizationConfiguration(2, 4),
        ).execute(specification)

        first_candidates = tuple(item.candidate for item in first.evaluations)
        second_candidates = tuple(item.candidate for item in second.evaluations)
        self.assertNotEqual(first_candidates, second_candidates)
        self.assertEqual(len(first_candidates), 4)
        self.assertEqual(len(set(first_candidates)), len(first_candidates))

    def test_exhaustion_empty_space_and_metadata_are_deterministic(self) -> None:
        exhausted = RandomOptimizationStrategy(
            _sampler(),
            _RecordingEvaluator(),
            RandomOptimizationConfiguration(5, 20),
        ).execute(_specification())
        empty_space = RandomOptimizationStrategy(
            _sampler(),
            _RecordingEvaluator(),
            RandomOptimizationConfiguration(5, 1),
        ).execute(_specification(ParameterSpace(())))

        self.assertEqual(len(exhausted.evaluations), 6)
        self.assertEqual(len(empty_space.evaluations), 1)
        self.assertEqual(empty_space.evaluations[0].candidate.assignments, ())
        self.assertEqual(exhausted.strategy_metadata.name, "random")

    def test_random_strategy_plugs_into_the_unchanged_optimization_runner(self) -> None:
        result = StandardOptimizationRunner(
            RandomOptimizationStrategy(
                _sampler(),
                _RecordingEvaluator(),
                RandomOptimizationConfiguration(7, 2),
            ),
            _Objective(),
            StandardObjectiveRanker(ObjectiveDirection.MAXIMIZE),
        ).run(_specification())

        self.assertEqual(len(result.search_run.evaluations), 2)
        self.assertEqual(result.strategy_metadata.name, "random")

    def test_strategy_rejects_invalid_configuration(self) -> None:
        with self.assertRaisesRegex(TypeError, "seed"):
            RandomOptimizationConfiguration(True, 1)  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "maximum_samples"):
            RandomOptimizationConfiguration(1, True)  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "negative"):
            RandomOptimizationConfiguration(1, -1)
        with self.assertRaisesRegex(TypeError, "candidate_evaluator"):
            RandomOptimizationStrategy(
                _sampler(),
                None,
                RandomOptimizationConfiguration(1, 1),
            )  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "random_candidate_sampler"):
            RandomOptimizationStrategy(
                None,
                _RecordingEvaluator(),
                RandomOptimizationConfiguration(1, 1),
            )  # type: ignore[arg-type]

    def test_public_exports_are_intentional(self) -> None:
        from src.engines.backtesting import (
            RandomOptimizationConfiguration as PackageConfiguration,
        )
        from src.engines.backtesting import (
            RandomOptimizationStrategy as PackageStrategy,
        )

        self.assertIs(PackageConfiguration, RandomOptimizationConfiguration)
        self.assertIs(PackageStrategy, RandomOptimizationStrategy)


class _RecordingEvaluator:
    """Test-only evaluator retaining candidates without scoring or ranking them."""

    def __init__(self) -> None:
        self.candidates: list[CandidateParameterSet] = []
        self.outcome = _outcome()

    def evaluate(self, candidate: CandidateParameterSet) -> CandidateEvaluation:
        """Retain the exact sampled candidate and return a fixed immutable outcome."""
        self.candidates.append(candidate)
        return CandidateEvaluation(candidate, self.outcome)


class _Objective:
    """Test-only objective that preserves existing candidate evaluations."""

    def score(self, evaluation: CandidateEvaluation) -> ObjectiveScore:
        """Return one explicit score without defining a production objective."""
        return ObjectiveScore(evaluation, 1.0, ObjectiveDirection.MAXIMIZE)


class _SkippedExecutionEngine:
    """Minimal dependency required to construct existing immutable backtest runs."""

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Return a skipped result without executing a trade."""
        return ExecutionResult(request, ExecutionStatus.SKIPPED)


class _SelectionPolicy:
    """Minimal structural policy required by an existing optimization specification."""

    def select(self, ranking: ObjectiveRanking) -> ObjectiveSelection:
        """Return an empty selection for the exact supplied ranking."""
        return ObjectiveSelection(ranking)


def _specification(
    parameter_space: ParameterSpace | None = None,
) -> OptimizationSpecification:
    """Create one immutable random-search input without orchestration behavior."""
    return OptimizationSpecification(
        parameter_space or ParameterSpace(
            (
                DiscreteParameter("orb_minutes", (5, 15, 30)),
                DiscreteParameter("target_multiple", (1.0, 2.0)),
            )
        ),
        OptimizationConfiguration(ObjectiveDirection.MAXIMIZE, _SelectionPolicy()),
    )


def _outcome() -> BacktestRun:
    """Create one existing immutable backtest result for candidate evaluations."""
    context = BacktestContext(
        behavior_atlas=ORBBehaviorAtlas(records=()),
        strategy=ORBRuleStrategy(),
        execution_engine=_SkippedExecutionEngine(),
    )
    return BacktestRun(context, BacktestStatus.COMPLETED)


def _sampler() -> DeterministicRandomCandidateSampler:
    """Create the explicit finite indexer-backed sampler used by this suite."""
    return DeterministicRandomCandidateSampler(CartesianParameterSpaceIndexer())
