"""Contract tests for deterministic grid-search orchestration only."""

from dataclasses import FrozenInstanceError, is_dataclass
from unittest import TestCase

from src.engines.backtesting import (
    BacktestContext,
    BacktestRun,
    BacktestStatus,
    CandidateEvaluation,
    GridSearchRun,
    GridSearchRunner,
    OptimizationBudget,
    StandardGridSearchRunner,
)
from src.engines.execution import ExecutionRequest, ExecutionResult, ExecutionStatus
from src.engines.research import ORBBehaviorAtlas
from src.engines.strategy import (
    CandidateParameterSet,
    DiscreteParameter,
    GridCandidateGenerator,
    ORBRuleStrategy,
    ParameterSpace,
)


class GridSearchRunnerTests(TestCase):
    """Verify sequential orchestration without ranking or optimizer behavior."""

    def test_run_preserves_generation_order_and_evaluates_each_candidate_once(
        self,
    ) -> None:
        parameter_space = _space()
        generated = (
            CandidateParameterSet((("orb_minutes", 5),)),
            CandidateParameterSet((("orb_minutes", 15),)),
        )
        generator = _RecordingGenerator(generated)
        evaluator = _RecordingEvaluator()
        runner: GridSearchRunner = StandardGridSearchRunner(generator, evaluator)

        run = runner.run(parameter_space, _budget())

        self.assertIs(run.parameter_space, parameter_space)
        self.assertEqual(tuple(item.candidate for item in run.evaluations), generated)
        self.assertEqual(generator.spaces, [parameter_space])
        self.assertEqual(evaluator.candidates, list(generated))

    def test_empty_parameter_space_evaluates_its_one_generated_candidate(self) -> None:
        parameter_space = ParameterSpace(())
        candidate = CandidateParameterSet(())
        evaluator = _RecordingEvaluator()

        run = StandardGridSearchRunner(GridCandidateGenerator(), evaluator).run(
            parameter_space,
            _budget(),
        )

        self.assertEqual(
            tuple(item.candidate for item in run.evaluations),
            (candidate,),
        )
        self.assertEqual(evaluator.candidates, [candidate])

    def test_run_and_aggregate_are_deterministic_immutable_and_non_mutating(
        self,
    ) -> None:
        parameter_space = _space()
        generated = (CandidateParameterSet((("orb_minutes", 5),)),)
        runner = StandardGridSearchRunner(
            _RecordingGenerator(generated),
            _RecordingEvaluator(),
        )

        first = runner.run(parameter_space, _budget())
        second = runner.run(parameter_space, _budget())

        self.assertEqual(first, second)
        self.assertEqual(repr(first), repr(second))
        self.assertTrue(is_dataclass(first))
        self.assertFalse(hasattr(first, "__dict__"))
        self.assertEqual(parameter_space.parameters[0].values, (5, 15))
        with self.assertRaises(FrozenInstanceError):
            first.evaluations = ()  # type: ignore[misc]

    def test_runner_stops_and_propagates_evaluator_failure_without_a_partial_run(
        self,
    ) -> None:
        parameter_space = _space()
        first = CandidateParameterSet((("orb_minutes", 5),))
        second = CandidateParameterSet((("orb_minutes", 15),))
        evaluator = _FailingEvaluator()
        runner = StandardGridSearchRunner(
            _RecordingGenerator((first, second)),
            evaluator,
        )

        with self.assertRaisesRegex(RuntimeError, "evaluation failed"):
            runner.run(parameter_space, _budget())

        self.assertEqual(evaluator.candidates, [first])

    def test_run_rejects_intrinsic_misuse_and_inconsistent_evaluations(self) -> None:
        candidate = CandidateParameterSet((("orb_minutes", 5),))
        parameter_space = _space()

        with self.assertRaisesRegex(TypeError, "parameter_space"):
            StandardGridSearchRunner(
                _RecordingGenerator(()),
                _RecordingEvaluator(),
            ).run(
                None,  # type: ignore[arg-type]
                _budget(),
            )
        with self.assertRaisesRegex(TypeError, "budget"):
            StandardGridSearchRunner(
                _RecordingGenerator(()),
                _RecordingEvaluator(),
            ).run(parameter_space, None)  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "candidate_generator"):
            StandardGridSearchRunner(
                None,
                _RecordingEvaluator(),
            )  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "candidate_evaluator"):
            StandardGridSearchRunner(
                _RecordingGenerator(()),
                None,
            )  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "match"):
            StandardGridSearchRunner(
                _RecordingGenerator((candidate,)),
                _MismatchedEvaluator(),
            ).run(parameter_space, _budget())
        with self.assertRaisesRegex(TypeError, "evaluations"):
            GridSearchRun(parameter_space, [])  # type: ignore[arg-type]

    def test_public_exports_are_intentional(self) -> None:
        from src.engines.backtesting import GridSearchRun as PackageRun
        from src.engines.backtesting import GridSearchRunner as PackageRunner
        from src.engines.backtesting import StandardGridSearchRunner as PackageStandard

        self.assertIs(PackageRun, GridSearchRun)
        self.assertIs(PackageRunner, GridSearchRunner)
        self.assertIs(PackageStandard, StandardGridSearchRunner)


class _RecordingGenerator:
    """Test-only generator that retains supplied candidates in order."""

    def __init__(self, candidates: tuple[CandidateParameterSet, ...]) -> None:
        self.candidates = candidates
        self.spaces: list[ParameterSpace] = []

    def generate(
        self,
        parameter_space: ParameterSpace,
    ) -> tuple[CandidateParameterSet, ...]:
        """Record the supplied space and return configured candidates unchanged."""
        self.spaces.append(parameter_space)
        return self.candidates


class _RecordingEvaluator:
    """Test-only evaluator that retains exact candidate references in order."""

    def __init__(self) -> None:
        self.candidates: list[CandidateParameterSet] = []
        self.outcome = _outcome()

    def evaluate(self, candidate: CandidateParameterSet) -> CandidateEvaluation:
        """Record one candidate and return its fixed typed backtest outcome."""
        self.candidates.append(candidate)
        return CandidateEvaluation(candidate, self.outcome)


class _FailingEvaluator(_RecordingEvaluator):
    """Test-only evaluator that fails on its first invocation."""

    def evaluate(self, candidate: CandidateParameterSet) -> CandidateEvaluation:
        """Record the candidate before propagating one explicit failure."""
        self.candidates.append(candidate)
        raise RuntimeError("evaluation failed")


class _MismatchedEvaluator:
    """Test-only evaluator that returns an inconsistent candidate reference."""

    def evaluate(self, candidate: CandidateParameterSet) -> CandidateEvaluation:
        """Return a valid evaluation for a different candidate to test rejection."""
        del candidate
        return CandidateEvaluation(CandidateParameterSet(()), _outcome())


class _SkippedExecutionEngine:
    """Minimal execution dependency for structural BacktestRun construction."""

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Return a skipped result without executing a trade."""
        return ExecutionResult(request, ExecutionStatus.SKIPPED)


def _space() -> ParameterSpace:
    """Return one finite immutable source space for runner orchestration tests."""
    return ParameterSpace((DiscreteParameter("orb_minutes", (5, 15)),))


def _outcome() -> BacktestRun:
    """Create one existing complete run without candidate-evaluation logic."""
    context = BacktestContext(
        behavior_atlas=ORBBehaviorAtlas(records=()),
        strategy=ORBRuleStrategy(),
        execution_engine=_SkippedExecutionEngine(),
    )
    return BacktestRun(context, BacktestStatus.COMPLETED)


def _budget() -> OptimizationBudget:
    """Return one explicit evaluation budget for grid-runner contract tests."""
    return OptimizationBudget(2)
