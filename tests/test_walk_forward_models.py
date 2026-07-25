"""Contract tests for immutable half-open walk-forward domain values."""

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from unittest import TestCase

from src.engines.backtesting.walk_forward import (
    DateTimeRange,
    WalkForwardPlan,
    WalkForwardWindow,
)


class WalkForwardModelTests(TestCase):
    """Verify ranges and plans without slicing observations or scheduling windows."""

    def test_half_open_range_includes_start_and_excludes_end(self) -> None:
        """Keep the documented interval contract explicit and deterministic."""
        value = DateTimeRange(_time(0), _time(10))
        self.assertTrue(value.contains(_time(0)))
        self.assertFalse(value.contains(_time(10)))
        with self.assertRaises(ValueError):
            DateTimeRange(_time(0), _time(0))
        with self.assertRaises(ValueError):
            DateTimeRange(_time(10), _time(0))

    def test_windows_allow_contiguous_or_gapped_ranges_but_not_overlap(self) -> None:
        """Keep training before validation with neither calendar nor gap policy."""
        first = _window(0, 0, 5, 5, 10)
        second = _window(1, 10, 15, 20, 25)
        self.assertEqual(first.index, 0)
        self.assertEqual(second.index, 1)
        with self.assertRaises(ValueError):
            _window(2, 0, 6, 5, 10)

    def test_plans_are_empty_valid_ordered_unique_and_immutable(self) -> None:
        """Preserve supplied order only when training chronology increases."""
        first = _window(0, 0, 5, 5, 10)
        second = _window(1, 2, 7, 7, 12)
        plan = WalkForwardPlan((first, second))
        self.assertEqual(WalkForwardPlan().windows, ())
        self.assertEqual(plan.windows, (first, second))
        with self.assertRaises(FrozenInstanceError):
            plan.windows = ()
        with self.assertRaises(ValueError):
            WalkForwardPlan((first, first))
        with self.assertRaises(ValueError):
            WalkForwardPlan((second, first))


def _window(
    index: int,
    train_start: int,
    train_end: int,
    valid_start: int,
    valid_end: int,
) -> WalkForwardWindow:
    """Build one deterministic walk-forward window fixture."""
    return WalkForwardWindow(
        index,
        DateTimeRange(_time(train_start), _time(train_end)),
        DateTimeRange(_time(valid_start), _time(valid_end)),
    )


def _time(minutes: int) -> datetime:
    """Return an aware timestamp without session or calendar inference."""
    return datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=minutes)
