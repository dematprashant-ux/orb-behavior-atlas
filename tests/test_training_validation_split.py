"""Contract tests for injected training/validation dataset split composition."""

from datetime import date, datetime, timedelta, timezone
from unittest import TestCase

from src.engines.backtesting.walk_forward import (
    DatasetWindow,
    DateTimeRange,
    StandardTrainingValidationSplitEngine,
    TrainingValidationSplitEngine,
    WalkForwardWindow,
)
from src.engines.data.models import Candle, Instrument, Timeframe


class TrainingValidationSplitTests(TestCase):
    """Verify training-first two-call orchestration without availability policy."""

    def test_split_delegates_training_then_validation_and_retains_window(self) -> None:
        """Pass exact ranges to the injected builder and preserve empty selections."""
        calls = []
        engine: TrainingValidationSplitEngine = StandardTrainingValidationSplitEngine(
            _RecordingBuilder(calls)
        )
        window = _window()
        split = engine.split((_candle(0), _candle(10)), window)
        self.assertEqual(calls, [window.training_range, window.validation_range])
        self.assertIs(split.source_window, window)
        self.assertEqual(split.training.observations, ())
        self.assertEqual(split.validation.observations, ())

    def test_failures_propagate_and_boundary_types_are_explicit(self) -> None:
        """Do not catch failures, shift ranges, or return partial split outputs."""
        engine = StandardTrainingValidationSplitEngine(_FailingBuilder())
        with self.assertRaises(RuntimeError):
            engine.split((), _window())
        with self.assertRaises(TypeError):
            StandardTrainingValidationSplitEngine(None)
        with self.assertRaises(TypeError):
            StandardTrainingValidationSplitEngine(_RecordingBuilder([])).split(
                [],
                _window(),
            )


class _RecordingBuilder:
    """Test-only builder retaining requested ranges in exact call order."""

    def __init__(self, calls):
        self.calls = calls

    def build(self, observations, requested_range):
        self.calls.append(requested_range)
        return DatasetWindow(requested_range, ())


class _FailingBuilder:
    """Test-only failure source for split failure propagation."""

    def build(self, observations, requested_range):
        raise RuntimeError("builder failure")


def _window() -> WalkForwardWindow:
    """Build a deterministic contiguous source window."""
    return WalkForwardWindow(
        0,
        DateTimeRange(_time(0), _time(5)),
        DateTimeRange(_time(5), _time(10)),
    )


def _candle(minutes: int) -> Candle:
    """Build a canonical candle fixture."""
    return Candle(
        Instrument.BANKNIFTY,
        Timeframe.M5,
        _time(minutes),
        date(2026, 1, 1),
        1.0,
        1.0,
        1.0,
        1.0,
        0,
    )


def _time(minutes: int) -> datetime:
    return datetime(2026, 1, 1, 9, 15, tzinfo=timezone.utc) + timedelta(minutes=minutes)
