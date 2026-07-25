"""Contract tests for deterministic rolling walk-forward schedule generation."""

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from unittest import TestCase

from src.engines.backtesting.walk_forward import (
    DateTimeRange,
    RollingWindowGenerator,
    StandardRollingWindowGenerator,
    WalkForwardConfiguration,
)


class RollingWindowGeneratorTests(TestCase):
    """Verify complete calendar-time rolling windows without dataset awareness."""

    def test_generates_complete_windows_with_stable_indices(self) -> None:
        """Include exact-end fits and exclude incomplete final validation windows."""
        generator: RollingWindowGenerator = StandardRollingWindowGenerator()
        plan = generator.generate(_configuration(30, 10, 5, 5))
        self.assertEqual(tuple(window.index for window in plan.windows), (0, 1, 2, 3))
        self.assertEqual(plan.windows[0].training_range, DateTimeRange(_time(0), _time(10)))
        self.assertEqual(plan.windows[-1].validation_range, DateTimeRange(_time(25), _time(30)))

    def test_allows_overlapping_or_gapped_validation_by_explicit_step(self) -> None:
        """Use the configured step directly rather than imposing schedule policy."""
        overlapping = StandardRollingWindowGenerator().generate(_configuration(30, 10, 10, 5))
        gapped = StandardRollingWindowGenerator().generate(_configuration(35, 10, 5, 10))
        self.assertEqual(len(overlapping.windows), 3)
        self.assertEqual(len(gapped.windows), 3)
        self.assertEqual(StandardRollingWindowGenerator().generate(_configuration(10, 10, 5, 5)).windows, ())

    def test_configuration_is_immutable_and_rejects_intrinsic_misuse(self) -> None:
        """Require positive explicit durations and a canonical overall range."""
        configuration = _configuration(20, 10, 5, 5)
        with self.assertRaises(FrozenInstanceError):
            configuration.step_duration = timedelta(1)
        with self.assertRaises(ValueError):
            _configuration(20, 0, 5, 5)
        with self.assertRaises(TypeError):
            StandardRollingWindowGenerator().generate(object())


def _configuration(total: int, training: int, validation: int, step: int) -> WalkForwardConfiguration:
    """Build explicit minute-based calendar-time schedule configuration."""
    return WalkForwardConfiguration(DateTimeRange(_time(0), _time(total)), timedelta(minutes=training), timedelta(minutes=validation), timedelta(minutes=step))


def _time(minutes: int) -> datetime:
    return datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=minutes)
