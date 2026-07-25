"""Contract tests for explicit deterministic optimization policy configuration."""

from dataclasses import FrozenInstanceError, dataclass, is_dataclass
from unittest import TestCase

from src.engines.backtesting import (
    BacktestContext,
    BacktestRun,
    BacktestStatus,
    CandidateEvaluation,
    ObjectiveDirection,
    ObjectiveRanking,
    ObjectiveScore,
    ObjectiveSelection,
    OptimizationConfiguration,
    OptimizationSearchRun,
    OptimizationSpecification,
    StandardObjectiveRanker,
    StandardOptimizationRunner,
)
from src.engines.backtesting.grid_search import GridSearchRun
from src.engines.execution import ExecutionRequest, ExecutionResult, ExecutionStatus
from src.engines.research import ORBBehaviorAtlas
from src.engines.strategy import CandidateParameterSet, ORBRuleStrategy, ParameterSpace


class OptimizationConfigurationTests(TestCase):
    """Verify explicit policy ownership without changing pipeline semantics."""

    def test_configuration_is_immutable_and_retains_explicit_values(self) -> None:
        policy = _RecordingSelectionPolicy([])
        configuration = OptimizationConfiguration(ObjectiveDirection.MINIMIZE, policy)

        self.assertTrue(is_dataclass(configuration))
        self.assertFalse(hasattr(configuration, "__dict__"))
        self.assertIs(configuration.selection_policy, policy)
        self.assertEqual(configuration.direction, ObjectiveDirection.MINIMIZE)
        self.assertEqual(repr(configuration), repr(configuration))
        with self.assertRaises(FrozenInstanceError):
            configuration.direction = ObjectiveDirection.MAXIMIZE  # type: ignore[misc]

    def test_configuration_equality_follows_its_immutable_values(self) -> None:
        first = OptimizationConfiguration(
            ObjectiveDirection.MAXIMIZE,
            _ValueSelectionPolicy(),
        )
        second = OptimizationConfiguration(
            ObjectiveDirection.MAXIMIZE,
            _ValueSelectionPolicy(),
        )

        self.assertEqual(first, second)

    def test_configuration_rejects_missing_or_untyped_direction(self) -> None:
        with self.assertRaisesRegex(TypeError, "direction"):
            OptimizationConfiguration(
                "maximize", _ValueSelectionPolicy()
            )  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "selection_policy"):
            OptimizationConfiguration(
                ObjectiveDirection.MAXIMIZE, None
            )  # type: ignore[arg-type]

    def test_empty_run_uses_configuration_direction_and_exact_policy(self) -> None:
        events: list[str] = []
        parameter_space = ParameterSpace(())
        policy = _RecordingSelectionPolicy(events)
        runner = StandardOptimizationRunner(
            _GridRunner(GridSearchRun(parameter_space), events),
            _Objective(events, ObjectiveDirection.MINIMIZE),
            _Ranker(events, ObjectiveDirection.MINIMIZE),
        )

        specification = _specification(
            parameter_space,
            ObjectiveDirection.MINIMIZE,
            policy,
        )
        result = runner.run(specification)

        self.assertEqual(events, ["grid", "rank", "select"])
        self.assertEqual(result.ranking.direction, ObjectiveDirection.MINIMIZE)
        self.assertIs(result.selection.ranking, result.ranking)
        self.assertIs(specification.configuration.selection_policy, policy)

    def test_mismatched_score_stops_before_ranking_and_selection(self) -> None:
        events: list[str] = []
        parameter_space = ParameterSpace(())
        evaluation = _evaluation()
        runner = StandardOptimizationRunner(
            _GridRunner(GridSearchRun(parameter_space, (evaluation,)), events),
            _Objective(events, ObjectiveDirection.MINIMIZE),
            _Ranker(events, ObjectiveDirection.MAXIMIZE),
        )

        with self.assertRaisesRegex(ValueError, "configuration"):
            runner.run(
                _specification(
                    parameter_space,
                    ObjectiveDirection.MAXIMIZE,
                    _RecordingSelectionPolicy(events),
                )
            )

        self.assertEqual(events, ["grid", "objective"])

    def test_populated_minimize_run_uses_the_configured_policy_once(self) -> None:
        events: list[str] = []
        parameter_space = ParameterSpace(())
        evaluation = _evaluation()
        policy = _RecordingSelectionPolicy(events)
        runner = StandardOptimizationRunner(
            _GridRunner(GridSearchRun(parameter_space, (evaluation,)), events),
            _Objective(events, ObjectiveDirection.MINIMIZE),
            _Ranker(events, ObjectiveDirection.MINIMIZE),
        )

        result = runner.run(
            _specification(parameter_space, ObjectiveDirection.MINIMIZE, policy)
        )

        self.assertEqual(events, ["grid", "objective", "rank", "select"])
        self.assertIs(result.selection.ranking, result.ranking)
        self.assertEqual(result.ranking.direction, ObjectiveDirection.MINIMIZE)

    def test_mismatched_ranker_direction_stops_before_selection(self) -> None:
        events: list[str] = []
        parameter_space = ParameterSpace(())
        evaluation = _evaluation()
        runner = StandardOptimizationRunner(
            _GridRunner(GridSearchRun(parameter_space, (evaluation,)), events),
            _Objective(events, ObjectiveDirection.MAXIMIZE),
            _MismatchedRanker(events),
        )

        with self.assertRaisesRegex(ValueError, "ranking direction"):
            runner.run(
                _specification(
                    parameter_space,
                    ObjectiveDirection.MAXIMIZE,
                    _RecordingSelectionPolicy(events),
                )
            )

        self.assertEqual(events, ["grid", "objective", "rank"])

    def test_public_export_is_intentional(self) -> None:
        from src.engines.backtesting import OptimizationConfiguration as PackageConfig

        self.assertIs(PackageConfig, OptimizationConfiguration)


@dataclass(frozen=True, slots=True)
class _ValueSelectionPolicy:
    """Minimal structurally compatible policy with deterministic value equality."""

    def select(self, ranking: ObjectiveRanking) -> ObjectiveSelection:
        """Return an empty selection for the exact supplied ranking."""
        return ObjectiveSelection(ranking)


class _RecordingSelectionPolicy:
    """Custom structurally compatible policy that records selection calls."""

    def __init__(self, events: list[str]) -> None:
        self.events = events

    def select(self, ranking: ObjectiveRanking) -> ObjectiveSelection:
        """Record exactly one selection without changing the supplied ranking."""
        self.events.append("select")
        return ObjectiveSelection(ranking)


class _GridRunner:
    """Test double retaining a supplied immutable grid-search result."""

    def __init__(self, result: GridSearchRun, events: list[str]) -> None:
        self.result = result
        self.events = events

    def execute(
        self,
        specification: OptimizationSpecification,
    ) -> OptimizationSearchRun:
        """Record one call and return the source-owned configured result."""
        self.events.append("grid")
        if specification.parameter_space is not self.result.parameter_space:
            raise AssertionError("unexpected parameter space")
        return OptimizationSearchRun(self.result.evaluations)


class _Objective:
    """Test-only objective returning an explicit fixed score direction."""

    def __init__(self, events: list[str], direction: ObjectiveDirection) -> None:
        self.events = events
        self.direction = direction

    def score(self, evaluation: CandidateEvaluation) -> ObjectiveScore:
        """Record one score call without providing a production formula."""
        self.events.append("objective")
        return ObjectiveScore(evaluation, 1.0, self.direction)


class _Ranker:
    """Test-only ranker retaining its injected direction and recording calls."""

    def __init__(self, events: list[str], direction: ObjectiveDirection) -> None:
        self.events = events
        self.direction = direction

    def rank(self, scores: tuple[ObjectiveScore, ...]) -> ObjectiveRanking:
        """Record one call and use the existing deterministic ranker."""
        self.events.append("rank")
        return StandardObjectiveRanker(self.direction).rank(scores)


class _MismatchedRanker:
    """Test-only ranker returning a valid ranking with a wrong direction."""

    def __init__(self, events: list[str]) -> None:
        self.events = events

    def rank(self, scores: tuple[ObjectiveScore, ...]) -> ObjectiveRanking:
        """Record one call and deliberately expose a configuration mismatch."""
        del scores
        self.events.append("rank")
        return ObjectiveRanking(ObjectiveDirection.MINIMIZE)


def _specification(
    parameter_space: ParameterSpace,
    direction: ObjectiveDirection,
    selection_policy: _RecordingSelectionPolicy,
) -> OptimizationSpecification:
    """Create one immutable specification for an existing test parameter space."""
    return OptimizationSpecification(
        parameter_space,
        OptimizationConfiguration(direction, selection_policy),
    )


def _evaluation() -> CandidateEvaluation:
    """Return one existing immutable evaluation without executing a backtest."""
    context = BacktestContext(
        behavior_atlas=ORBBehaviorAtlas(records=()),
        strategy=ORBRuleStrategy(),
        execution_engine=_SkippedExecutionEngine(),
    )
    return CandidateEvaluation(
        CandidateParameterSet((("candidate", "one"),)),
        BacktestRun(context, BacktestStatus.COMPLETED),
    )


class _SkippedExecutionEngine:
    """Minimal dependency required to construct an existing BacktestContext."""

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Return a skipped immutable result without execution behavior."""
        return ExecutionResult(request, ExecutionStatus.SKIPPED)
