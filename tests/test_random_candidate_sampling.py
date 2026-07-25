"""Contract tests for deterministic random candidate sampling."""

import random
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
    RandomCandidateSampler,
    RandomOptimizationConfiguration,
    RandomOptimizationStrategy,
)
from src.engines.execution import ExecutionRequest, ExecutionResult, ExecutionStatus
from src.engines.research import ORBBehaviorAtlas
from src.engines.strategy import (
    CandidateParameterSet,
    DiscreteParameter,
    ORBRuleStrategy,
    ParameterSpace,
)


class RandomCandidateSamplingTests(TestCase):
    """Verify sampling is distinct from ordered candidate evaluation."""

    def test_sampler_protocol_and_public_exports_are_intentional(self) -> None:
        sampler: RandomCandidateSampler = DeterministicRandomCandidateSampler()
        from src.engines.backtesting import (
            DeterministicRandomCandidateSampler as PackageSampler,
        )
        from src.engines.backtesting import RandomCandidateSampler as PackageProtocol

        self.assertIsInstance(sampler, DeterministicRandomCandidateSampler)
        self.assertIs(PackageSampler, DeterministicRandomCandidateSampler)
        self.assertIs(PackageProtocol, RandomCandidateSampler)

    def test_sampler_preserves_the_m20_1_seeded_sequence(self) -> None:
        sampled = DeterministicRandomCandidateSampler().sample(
            _parameter_space(),
            RandomOptimizationConfiguration(17, 4),
        )

        self.assertEqual(
            sampled,
            (
                CandidateParameterSet(
                    (("orb_minutes", 30), ("target_multiple", 1.0))
                ),
                CandidateParameterSet(
                    (("orb_minutes", 15), ("target_multiple", 2.0))
                ),
                CandidateParameterSet(
                    (("orb_minutes", 15), ("target_multiple", 1.0))
                ),
                CandidateParameterSet(
                    (("orb_minutes", 5), ("target_multiple", 2.0))
                ),
            ),
        )

    def test_sampler_is_deterministic_unique_and_does_not_mutate_global_state(
        self,
    ) -> None:
        sampler = DeterministicRandomCandidateSampler()
        configuration = RandomOptimizationConfiguration(5, 20)
        state = random.getstate()
        first = sampler.sample(_parameter_space(), configuration)
        second = sampler.sample(_parameter_space(), configuration)

        self.assertEqual(first, second)
        self.assertEqual(len(first), 6)
        self.assertEqual(len(set(first)), len(first))
        self.assertEqual(random.getstate(), state)

    def test_sampler_handles_empty_and_zero_sample_spaces(self) -> None:
        sampler = DeterministicRandomCandidateSampler()

        self.assertEqual(
            sampler.sample(ParameterSpace(()), RandomOptimizationConfiguration(5, 1)),
            (CandidateParameterSet(()),),
        )
        self.assertEqual(
            sampler.sample(_parameter_space(), RandomOptimizationConfiguration(5, 0)),
            (),
        )

    def test_empty_sample_skips_evaluation_and_retains_strategy_metadata(self) -> None:
        evaluator = _RecordingEvaluator()
        strategy = RandomOptimizationStrategy(
            DeterministicRandomCandidateSampler(),
            evaluator,
            RandomOptimizationConfiguration(5, 0),
        )

        result = strategy.execute(_specification())

        self.assertEqual(result.evaluations, ())
        self.assertEqual(evaluator.candidates, [])
        self.assertIs(result.strategy_metadata, strategy.metadata)

    def test_strategy_invokes_an_injected_sampler_once_in_sampled_order(self) -> None:
        candidates = (
            CandidateParameterSet((("orb_minutes", 5), ("target_multiple", 1.0))),
            CandidateParameterSet((("orb_minutes", 15), ("target_multiple", 2.0))),
        )
        sampler = _RecordingSampler(candidates)
        evaluator = _RecordingEvaluator()
        specification = _specification()
        configuration = RandomOptimizationConfiguration(11, 2)

        strategy = RandomOptimizationStrategy(
            sampler,
            evaluator,
            configuration,
        )
        result = strategy.execute(specification)

        self.assertEqual(
            sampler.calls,
            [(specification.parameter_space, configuration)],
        )
        self.assertEqual(len(evaluator.candidates), len(candidates))
        self.assertTrue(
            all(
                actual is expected
                for actual, expected in zip(evaluator.candidates, candidates)
            )
        )
        self.assertTrue(
            all(
                actual is expected
                for actual, expected in zip(result.evaluations, evaluator.evaluations)
            )
        )
        self.assertIs(result.strategy_metadata, strategy.metadata)

    def test_strategy_propagates_sampler_and_evaluator_failures_unchanged(self) -> None:
        specification = _specification()
        evaluator = _RecordingEvaluator()
        with self.assertRaisesRegex(RuntimeError, "sampler failure"):
            RandomOptimizationStrategy(
                _FailingSampler(),
                evaluator,
                RandomOptimizationConfiguration(1, 1),
            ).execute(specification)
        self.assertEqual(evaluator.candidates, [])

        candidates = (
            CandidateParameterSet((("orb_minutes", 5), ("target_multiple", 1.0))),
            CandidateParameterSet((("orb_minutes", 15), ("target_multiple", 1.0))),
        )
        failing_evaluator = _FailingEvaluator()
        with self.assertRaisesRegex(RuntimeError, "evaluator failure"):
            RandomOptimizationStrategy(
                _RecordingSampler(candidates),
                failing_evaluator,
                RandomOptimizationConfiguration(1, 2),
            ).execute(specification)
        self.assertEqual(failing_evaluator.candidates, [candidates[0]])


class _RecordingSampler:
    """Test-only sampler retaining explicit invocation data."""

    def __init__(self, candidates: tuple[CandidateParameterSet, ...]) -> None:
        self.candidates = candidates
        self.calls: list[tuple[ParameterSpace, RandomOptimizationConfiguration]] = []

    def sample(
        self,
        parameter_space: ParameterSpace,
        configuration: RandomOptimizationConfiguration,
    ) -> tuple[CandidateParameterSet, ...]:
        """Return exact preconstructed candidates without evaluating them."""
        self.calls.append((parameter_space, configuration))
        return self.candidates


class _FailingSampler:
    """Test-only sampler proving failure propagation without fallback sampling."""

    def sample(
        self,
        parameter_space: ParameterSpace,
        configuration: RandomOptimizationConfiguration,
    ) -> tuple[CandidateParameterSet, ...]:
        """Fail directly without inspecting the supplied values."""
        del parameter_space, configuration
        raise RuntimeError("sampler failure")


class _RecordingEvaluator:
    """Test-only evaluator retaining exact candidates and evaluations."""

    def __init__(self) -> None:
        self.candidates: list[CandidateParameterSet] = []
        self.evaluations: list[CandidateEvaluation] = []
        self.outcome = _outcome()

    def evaluate(self, candidate: CandidateParameterSet) -> CandidateEvaluation:
        """Retain one candidate and produce one existing typed evaluation."""
        self.candidates.append(candidate)
        evaluation = CandidateEvaluation(candidate, self.outcome)
        self.evaluations.append(evaluation)
        return evaluation


class _FailingEvaluator:
    """Test-only evaluator proving immediate stop at the first failure."""

    def __init__(self) -> None:
        self.candidates: list[CandidateParameterSet] = []

    def evaluate(self, candidate: CandidateParameterSet) -> CandidateEvaluation:
        """Retain the first candidate then fail unchanged."""
        self.candidates.append(candidate)
        raise RuntimeError("evaluator failure")


class _SkippedExecutionEngine:
    """Minimal dependency required to construct an existing immutable result."""

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Return one skipped execution result without trade simulation."""
        return ExecutionResult(request, ExecutionStatus.SKIPPED)


class _SelectionPolicy:
    """Minimal policy needed to construct the existing optimization specification."""

    def select(self, ranking: ObjectiveRanking) -> ObjectiveSelection:
        """Retain the supplied ranking without selecting entries."""
        return ObjectiveSelection(ranking)


def _parameter_space() -> ParameterSpace:
    """Return the finite ordered space used to preserve M20.1 behavior."""
    return ParameterSpace(
        (
            DiscreteParameter("orb_minutes", (5, 15, 30)),
            DiscreteParameter("target_multiple", (1.0, 2.0)),
        )
    )


def _specification() -> OptimizationSpecification:
    """Return an immutable input without adding optimizer behavior."""
    return OptimizationSpecification(
        _parameter_space(),
        OptimizationConfiguration(ObjectiveDirection.MAXIMIZE, _SelectionPolicy()),
    )


def _outcome() -> BacktestRun:
    """Construct one existing immutable backtest result for test evaluations."""
    context = BacktestContext(
        behavior_atlas=ORBBehaviorAtlas(records=()),
        strategy=ORBRuleStrategy(),
        execution_engine=_SkippedExecutionEngine(),
    )
    return BacktestRun(context, BacktestStatus.COMPLETED)
