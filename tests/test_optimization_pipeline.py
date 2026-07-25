"""Contract tests for deterministic optimization orchestration only."""

from dataclasses import FrozenInstanceError, is_dataclass
from unittest import TestCase

from src.engines.backtesting import (
    BacktestContext,
    BacktestRun,
    BacktestStatus,
    CandidateEvaluation,
    GridSearchRun,
    ObjectiveDirection,
    ObjectiveRanking,
    ObjectiveScore,
    ObjectiveSelection,
    OptimizationConfiguration,
    OptimizationRun,
    OptimizationRunner,
    OptimizationSpecification,
    StandardObjectiveRanker,
    StandardOptimizationRunner,
)
from src.engines.execution import ExecutionRequest, ExecutionResult, ExecutionStatus
from src.engines.research import ORBBehaviorAtlas
from src.engines.strategy import (
    CandidateParameterSet,
    DiscreteParameter,
    ORBRuleStrategy,
    ParameterSpace,
)


class OptimizationPipelineTests(TestCase):
    """Verify composition without adding search, scoring, or ranking behavior."""

    def test_runner_delegates_once_in_order_and_preserves_cross_stage_references(
        self,
    ) -> None:
        events: list[str] = []
        parameter_space = _space()
        grid_search_run = _grid_search_run(parameter_space)
        runner: OptimizationRunner = StandardOptimizationRunner(
            _GridSearchRunner(grid_search_run, events),
            _Objective(events),
            _Ranker(events),
        )

        result = runner.run(_specification(parameter_space, events))

        self.assertEqual(
            events,
            ["grid", "objective", "objective", "rank", "select"],
        )
        self.assertIs(result.grid_search_run, grid_search_run)
        self.assertEqual(
            tuple(score.evaluation for score in result.objective_scores),
            grid_search_run.evaluations,
        )
        for score, evaluation in zip(
            result.objective_scores,
            grid_search_run.evaluations,
        ):
            self.assertIs(score.evaluation, evaluation)
        self.assertEqual(
            tuple(item.source_score for item in result.ranking.ranked_scores),
            tuple(reversed(result.objective_scores)),
        )
        self.assertIs(result.selection.ranking, result.ranking)

    def test_run_is_immutable_deterministic_and_accepts_empty_search_results(
        self,
    ) -> None:
        parameter_space = ParameterSpace(())
        grid_search_run = GridSearchRun(parameter_space, ())
        runner = StandardOptimizationRunner(
            _GridSearchRunner(grid_search_run, []),
            _Objective([]),
            _Ranker([]),
        )

        first = runner.run(_specification(parameter_space, []))
        second = runner.run(_specification(parameter_space, []))

        self.assertEqual(first, second)
        self.assertEqual(repr(first), repr(second))
        self.assertTrue(is_dataclass(first))
        self.assertFalse(hasattr(first, "__dict__"))
        self.assertEqual(first.objective_scores, ())
        self.assertEqual(first.ranking.ranked_scores, ())
        self.assertEqual(first.selection.selected_scores, ())
        with self.assertRaises(FrozenInstanceError):
            first.ranking = first.ranking  # type: ignore[misc]

    def test_runner_propagates_a_stage_failure_without_later_calls_or_partial_output(
        self,
    ) -> None:
        events: list[str] = []
        parameter_space = _space()
        runner = StandardOptimizationRunner(
            _GridSearchRunner(_grid_search_run(parameter_space), events),
            _FailingObjective(events),
            _Ranker(events),
        )

        with self.assertRaisesRegex(RuntimeError, "objective failure"):
            runner.run(_specification(parameter_space, events))

        self.assertEqual(events, ["grid", "objective"])

    def test_runner_rejects_mixed_score_directions_before_ranking(self) -> None:
        events: list[str] = []
        parameter_space = _space()
        runner = StandardOptimizationRunner(
            _GridSearchRunner(_grid_search_run(parameter_space), events),
            _MixedDirectionObjective(events),
            _Ranker(events),
        )

        with self.assertRaisesRegex(ValueError, "match"):
            runner.run(_specification(parameter_space, events))

        self.assertEqual(events, ["grid", "objective", "objective"])

    def test_run_rejects_intrinsic_and_cross_stage_misuse(self) -> None:
        parameter_space = _space()
        evaluation = _evaluation("one")
        grid_search_run = GridSearchRun(parameter_space, (evaluation,))

        with self.assertRaisesRegex(TypeError, "specification"):
            StandardOptimizationRunner(
                _GridSearchRunner(grid_search_run, []),
                _Objective([]),
                _Ranker([]),
            ).run(None)  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "grid_search_runner"):
            StandardOptimizationRunner(
                None,
                _Objective([]),
                _Ranker([]),
            )
        with self.assertRaisesRegex(ValueError, "parameter_space"):
            StandardOptimizationRunner(
                _ForeignGridSearchRunner(GridSearchRun(_space(), (evaluation,))),
                _Objective([]),
                _Ranker([]),
            ).run(_specification(parameter_space, []))
        with self.assertRaisesRegex(ValueError, "in order"):
            OptimizationRun(
                grid_search_run,
                (
                    ObjectiveScore(
                        _evaluation("other"),
                        1.0,
                        ObjectiveDirection.MAXIMIZE,
                    ),
                ),
                ObjectiveRanking(ObjectiveDirection.MAXIMIZE),
                ObjectiveSelection(ObjectiveRanking(ObjectiveDirection.MAXIMIZE)),
            )

    def test_public_exports_are_intentional(self) -> None:
        from src.engines.backtesting import OptimizationRun as PackageRun
        from src.engines.backtesting import OptimizationRunner as PackageRunner
        from src.engines.backtesting import (
            StandardOptimizationRunner as PackageStandard,
        )

        self.assertIs(PackageRun, OptimizationRun)
        self.assertIs(PackageRunner, OptimizationRunner)
        self.assertIs(PackageStandard, StandardOptimizationRunner)


class _GridSearchRunner:
    """Test-only grid-search boundary returning one configured immutable result."""

    def __init__(self, result: GridSearchRun, events: list[str]) -> None:
        self.result = result
        self.events = events

    def run(self, parameter_space: ParameterSpace) -> GridSearchRun:
        """Record one call and retain the supplied parameter-space identity."""
        self.events.append("grid")
        if parameter_space is not self.result.parameter_space:
            raise AssertionError("unexpected parameter space")
        return self.result


class _ForeignGridSearchRunner:
    """Test-only boundary returning a result for a different parameter space."""

    def __init__(self, result: GridSearchRun) -> None:
        self.result = result

    def run(self, parameter_space: ParameterSpace) -> GridSearchRun:
        """Return the configured foreign result without invoking any search logic."""
        del parameter_space
        return self.result


class _Objective:
    """Test-only objective that maps each existing evaluation to a fixed score."""

    def __init__(self, events: list[str]) -> None:
        self.events = events

    def score(self, evaluation: CandidateEvaluation) -> ObjectiveScore:
        """Record one scoring call without calculating a production formula."""
        self.events.append("objective")
        return ObjectiveScore(
            evaluation,
            float(len(self.events)),
            ObjectiveDirection.MAXIMIZE,
        )


class _FailingObjective(_Objective):
    """Test-only objective that fails at the first scoring call."""

    def score(self, evaluation: CandidateEvaluation) -> ObjectiveScore:
        """Record one call before propagating the intended collaborator failure."""
        del evaluation
        self.events.append("objective")
        raise RuntimeError("objective failure")


class _MixedDirectionObjective(_Objective):
    """Test-only objective that exposes incompatible direction values."""

    def score(self, evaluation: CandidateEvaluation) -> ObjectiveScore:
        """Return alternating directions to exercise ranker compatibility checks."""
        self.events.append("objective")
        direction = (
            ObjectiveDirection.MAXIMIZE
            if len(self.events) == 2
            else ObjectiveDirection.MINIMIZE
        )
        return ObjectiveScore(evaluation, float(len(self.events)), direction)


class _Ranker:
    """Test-only ranker retaining exactly the received score references."""

    def __init__(self, events: list[str]) -> None:
        self.events = events

    def rank(self, scores: tuple[ObjectiveScore, ...]) -> ObjectiveRanking:
        """Delegate to the existing standard ranker after recording one call."""
        self.events.append("rank")
        return StandardObjectiveRanker(ObjectiveDirection.MAXIMIZE).rank(scores)


class _SelectionPolicy:
    """Test-only selector retaining the exact completed ranking reference."""

    def __init__(self, events: list[str]) -> None:
        self.events = events

    def select(self, ranking: ObjectiveRanking) -> ObjectiveSelection:
        """Record selection and retain the source ranking without policy logic."""
        self.events.append("select")
        return ObjectiveSelection(ranking, ranking.ranked_scores[:1])


class _SkippedExecutionEngine:
    """Minimal execution dependency for structural BacktestRun construction."""

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Return a skipped result without executing a trade."""
        return ExecutionResult(request, ExecutionStatus.SKIPPED)


def _space() -> ParameterSpace:
    """Create a source parameter space without candidate-generation behavior."""
    return ParameterSpace((DiscreteParameter("orb_minutes", (5, 15)),))


def _configuration(events: list[str]) -> OptimizationConfiguration:
    """Create one explicit policy configuration for standard test execution."""
    return OptimizationConfiguration(
        ObjectiveDirection.MAXIMIZE,
        _SelectionPolicy(events),
    )


def _specification(
    parameter_space: ParameterSpace,
    events: list[str],
) -> OptimizationSpecification:
    """Create one immutable test specification with explicit policy settings."""
    return OptimizationSpecification(parameter_space, _configuration(events))


def _grid_search_run(parameter_space: ParameterSpace) -> GridSearchRun:
    """Create ordered existing evaluations without executing grid search."""
    return GridSearchRun(parameter_space, (_evaluation("one"), _evaluation("two")))


def _evaluation(name: str) -> CandidateEvaluation:
    """Create one existing candidate evaluation without objective execution."""
    context = BacktestContext(
        behavior_atlas=ORBBehaviorAtlas(records=()),
        strategy=ORBRuleStrategy(),
        execution_engine=_SkippedExecutionEngine(),
    )
    return CandidateEvaluation(
        CandidateParameterSet((("candidate", name),)),
        BacktestRun(context, BacktestStatus.COMPLETED),
    )
