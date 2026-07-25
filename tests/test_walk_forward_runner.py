"""Contract tests for deterministic walk-forward runner composition."""

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta
from unittest import TestCase

from src.engines.backtesting import (
    DatasetWindow,
    DateTimeRange,
    StandardWalkForwardRunner,
    WalkForwardDatasetSplit,
    WalkForwardIterationResult,
    WalkForwardPlan,
    WalkForwardRun,
    WalkForwardRunner,
    WalkForwardSelection,
    WalkForwardValidationResult,
    WalkForwardWindow,
)


class WalkForwardRunnerTests(TestCase):
    """Verify sequential delegation without scheduling or optimization behavior."""

    def test_runner_composes_each_window_in_exact_plan_order(self) -> None:
        calls: list[tuple[str, int]] = []
        split_engine = _RecordingSplitEngine(calls)
        trainer = _RecordingTrainer(calls)
        executor = _RecordingValidationExecutor(calls)
        runner: WalkForwardRunner = StandardWalkForwardRunner(
            split_engine,
            trainer,
            executor,
        )
        plan = _plan()
        observations = ()

        run = runner.run(plan, observations)

        self.assertIs(run.plan, plan)
        self.assertEqual(
            calls,
            [
                ("split", 0),
                ("train", 0),
                ("validate", 0),
                ("split", 1),
                ("train", 1),
                ("validate", 1),
            ],
        )
        self.assertEqual(tuple(item.source_window for item in run.iterations), plan.windows)
        self.assertEqual(run.iterations[0].selection.selection_id, "selection-0")
        self.assertIs(run.iterations[0].validation, split_engine.splits[0].validation)
        self.assertIs(run.iterations[0].training, split_engine.splits[0].training)

    def test_empty_plan_returns_empty_run_without_invoking_collaborators(self) -> None:
        calls: list[tuple[str, int]] = []
        runner = StandardWalkForwardRunner(
            _RecordingSplitEngine(calls),
            _RecordingTrainer(calls),
            _RecordingValidationExecutor(calls),
        )

        run = runner.run(WalkForwardPlan(), ())

        self.assertEqual(run.iterations, ())
        self.assertEqual(calls, [])

    def test_iteration_and_run_are_immutable_and_deterministic(self) -> None:
        split = _split(_window(0, 0))
        selection = WalkForwardSelection("selection-0")
        result = WalkForwardValidationResult(selection, split.validation)
        iteration = WalkForwardIterationResult(split, selection, result)
        run = WalkForwardRun(WalkForwardPlan((split.source_window,)), (iteration,))

        self.assertEqual(iteration, WalkForwardIterationResult(split, selection, result))
        self.assertEqual(repr(run), repr(WalkForwardRun(run.plan, (iteration,))))
        with self.assertRaises(FrozenInstanceError):
            iteration.selection = WalkForwardSelection("changed")  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            run.iterations = ()  # type: ignore[misc]

    def test_run_rejects_iterations_not_matching_its_plan_order(self) -> None:
        first, second = _plan().windows
        first_iteration = _iteration(first)
        second_iteration = _iteration(second)

        with self.assertRaisesRegex(ValueError, "plan order"):
            WalkForwardRun(WalkForwardPlan((first, second)), (second_iteration, first_iteration))

    def test_iteration_rejects_inconsistent_validation_result(self) -> None:
        split = _split(_window(0, 0))
        selection = WalkForwardSelection("selection-0")
        other_selection = WalkForwardSelection("selection-other")

        with self.assertRaisesRegex(ValueError, "selection"):
            WalkForwardIterationResult(
                split,
                selection,
                WalkForwardValidationResult(other_selection, split.validation),
            )

    def test_constructor_and_delegated_failures_are_not_suppressed(self) -> None:
        with self.assertRaisesRegex(TypeError, "split_engine"):
            StandardWalkForwardRunner(None, _RecordingTrainer([]), _RecordingValidationExecutor([]))

        runner = StandardWalkForwardRunner(
            _RecordingSplitEngine([]),
            _FailingTrainer(),
            _RecordingValidationExecutor([]),
        )
        with self.assertRaisesRegex(RuntimeError, "trainer failure"):
            runner.run(_plan(), ())

    def test_runner_rejects_invalid_boundary_and_protocol_result_types(self) -> None:
        runner = StandardWalkForwardRunner(
            _InvalidSplitEngine(),
            _RecordingTrainer([]),
            _RecordingValidationExecutor([]),
        )
        with self.assertRaisesRegex(TypeError, "observations"):
            runner.run(_plan(), [])
        with self.assertRaisesRegex(TypeError, "split_engine.split"):
            runner.run(_plan(), ())

    def test_public_exports_include_runner_contracts(self) -> None:
        from src.engines.backtesting.walk_forward import (
            StandardWalkForwardRunner as PackageRunner,
        )
        from src.engines.backtesting.walk_forward import (
            WalkForwardIterationResult as PackageIteration,
        )
        from src.engines.backtesting.walk_forward import WalkForwardRun as PackageRun
        from src.engines.backtesting.walk_forward import (
            WalkForwardRunner as PackageProtocol,
        )

        self.assertIs(PackageRunner, StandardWalkForwardRunner)
        self.assertIs(PackageIteration, WalkForwardIterationResult)
        self.assertIs(PackageRun, WalkForwardRun)
        self.assertIs(PackageProtocol, WalkForwardRunner)


class _RecordingSplitEngine:
    """Test double that records split delegation without dataset slicing."""

    def __init__(self, calls: list[tuple[str, int]]) -> None:
        self.calls = calls
        self.splits: list[WalkForwardDatasetSplit] = []

    def split(
        self,
        observations: tuple[object, ...],
        window: WalkForwardWindow,
    ) -> WalkForwardDatasetSplit:
        del observations
        self.calls.append(("split", window.index))
        split = _split(window)
        self.splits.append(split)
        return split


class _RecordingTrainer:
    """Test double that records training delegation and returns typed selections."""

    def __init__(self, calls: list[tuple[str, int]]) -> None:
        self.calls = calls

    def train(self, training_window: DatasetWindow) -> WalkForwardSelection:
        index = _index_for(training_window)
        self.calls.append(("train", index))
        return WalkForwardSelection(f"selection-{index}")


class _RecordingValidationExecutor:
    """Test double that records validation delegation and returns typed results."""

    def __init__(self, calls: list[tuple[str, int]]) -> None:
        self.calls = calls

    def validate(
        self,
        selection: WalkForwardSelection,
        validation_window: DatasetWindow,
    ) -> WalkForwardValidationResult:
        self.calls.append(("validate", _index_for(validation_window)))
        return WalkForwardValidationResult(selection, validation_window)


class _FailingTrainer:
    """Test double confirming collaborator failures propagate unchanged."""

    def train(self, training_window: DatasetWindow) -> WalkForwardSelection:
        del training_window
        raise RuntimeError("trainer failure")


class _InvalidSplitEngine:
    """Test double returning an invalid protocol result."""

    def split(self, observations, window):
        del observations, window
        return None


def _plan() -> WalkForwardPlan:
    """Build a two-window chronological fixture."""
    return WalkForwardPlan((_window(0, 0), _window(1, 10)))


def _window(index: int, start_minutes: int) -> WalkForwardWindow:
    """Build one contiguous source window with deterministic boundaries."""
    training_start = _time(start_minutes)
    training_end = _time(start_minutes + 5)
    validation_end = _time(start_minutes + 10)
    return WalkForwardWindow(
        index,
        DateTimeRange(training_start, training_end),
        DateTimeRange(training_end, validation_end),
    )


def _split(window: WalkForwardWindow) -> WalkForwardDatasetSplit:
    """Build a typed empty split retaining the exact supplied window."""
    return WalkForwardDatasetSplit(
        window,
        DatasetWindow(window.training_range, ()),
        DatasetWindow(window.validation_range, ()),
    )


def _iteration(window: WalkForwardWindow) -> WalkForwardIterationResult:
    """Build one intrinsically consistent iteration fixture."""
    split = _split(window)
    selection = WalkForwardSelection(f"selection-{window.index}")
    return WalkForwardIterationResult(
        split,
        selection,
        WalkForwardValidationResult(selection, split.validation),
    )


def _index_for(window: DatasetWindow) -> int:
    """Derive a fixture index from its explicit deterministic minute boundary."""
    start = window.requested_range.start
    return (start.hour * 60 + start.minute) // 10


def _time(minutes: int) -> datetime:
    """Return an aware fixture timestamp without session or market inference."""
    return datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=minutes)
