"""Contract tests for deterministic multi-position portfolio lifecycle states."""

from dataclasses import FrozenInstanceError, is_dataclass
from datetime import datetime, timedelta, timezone
from unittest import TestCase

from src.engines.data.models import Instrument
from src.engines.execution import ExecutionSide
from src.engines.portfolio import (
    FixedCapitalAllocationPolicy,
    PortfolioCloseEvent,
    PortfolioEngine,
    PortfolioOpenEvent,
    StandardPortfolioEngine,
    build_portfolio_snapshot,
)


class PortfolioEngineTests(TestCase):
    """Verify portfolio cash state transitions without performance analytics."""

    def test_no_events_retains_only_the_initial_snapshot(self) -> None:
        """Return the supplied immutable starting state when no event exists."""
        initial = _initial()

        snapshots = _engine(100.0).process(initial, ())

        self.assertEqual(snapshots, (initial,))
        self.assertIs(snapshots[0], initial)

    def test_open_and_profitable_close_account_for_cash_exactly_once(self) -> None:
        """Deduct entry capital and restore only explicit exit proceeds on closure."""
        snapshots = _engine(250.0).process(
            _initial(),
            (
                _open("one", 100.0, 1),
                _close("one", 110.0, 2),
            ),
        )

        self.assertEqual(snapshots[1].available_cash, 800.0)
        self.assertEqual(snapshots[1].positions[0].quantity, 2)
        self.assertEqual(snapshots[2].available_cash, 1_020.0)
        self.assertEqual(snapshots[2].positions, ())

    def test_losing_close_and_released_cash_support_multiple_positions(self) -> None:
        """Preserve active order and make closed-position cash reusable in sequence."""
        snapshots = _engine(300.0).process(
            _initial(),
            (
                _open("one", 100.0, 1),
                _open("two", 100.0, 2),
                _close("one", 90.0, 3),
                _open("three", 90.0, 4),
            ),
        )

        self.assertEqual(
            tuple(position.position_id for position in snapshots[2].positions),
            ("one", "two"),
        )
        self.assertEqual(snapshots[3].available_cash, 670.0)
        self.assertEqual(
            tuple(position.position_id for position in snapshots[4].positions),
            ("two", "three"),
        )

    def test_rejects_insufficient_cash_zero_allocation_and_invalid_lifecycle(self) -> None:
        """Reject events that cannot create or close a coherent active position."""
        initial = _initial()
        with self.assertRaises(ValueError):
            _engine(50.0).process(initial, (_open("one", 100.0, 1),))
        with self.assertRaises(ValueError):
            _engine(0.0).process(initial, (_open("one", 100.0, 1),))
        with self.assertRaises(ValueError):
            _engine(100.0).process(initial, (_close("unknown", 100.0, 1),))
        with self.assertRaises(ValueError):
            _engine(100.0).process(
                initial,
                (_open("one", 100.0, 1), _open("one", 100.0, 2)),
            )

    def test_processing_preserves_event_order_and_propagates_collaborator_failure(self) -> None:
        """Never reorder equal timestamps or suppress allocation-policy failures."""
        initial = _initial()
        same_time = _timestamp(1)
        snapshots = _engine(100.0).process(
            initial,
            (
                PortfolioOpenEvent(
                    "one",
                    Instrument.BANKNIFTY,
                    ExecutionSide.LONG,
                    100.0,
                    same_time,
                ),
                PortfolioCloseEvent("one", 100.0, same_time),
            ),
        )

        self.assertEqual(
            tuple(snapshot.timestamp for snapshot in snapshots[1:]),
            (same_time, same_time),
        )
        with self.assertRaises(RuntimeError):
            StandardPortfolioEngine(_FailingPolicy()).process(
                initial,
                (_open("one", 100.0, 1),),
            )

    def test_engine_is_protocol_compatible_immutable_and_rejects_boundary_misuse(self) -> None:
        """Expose an immutable injected service with deterministic input failures."""
        engine: PortfolioEngine = _engine(100.0)

        self.assertTrue(is_dataclass(engine))
        self.assertFalse(hasattr(engine, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            engine.allocation_policy = FixedCapitalAllocationPolicy(1.0)
        with self.assertRaises(TypeError):
            engine.process(object(), ())
        with self.assertRaises(TypeError):
            engine.process(_initial(), [])
        with self.assertRaises(ValueError):
            engine.process(_initial(), (_open("one", 100.0, -1),))


def _engine(capital: float) -> StandardPortfolioEngine:
    """Build one deterministic fixed-capital portfolio engine fixture."""
    return StandardPortfolioEngine(FixedCapitalAllocationPolicy(capital))


def _initial():
    """Build an empty initial portfolio with explicit available cash."""
    return build_portfolio_snapshot(_timestamp(), 1_000.0)


def _open(position_id: str, price: float, minute: int) -> PortfolioOpenEvent:
    """Build one deterministic open event fixture."""
    return PortfolioOpenEvent(
        position_id,
        Instrument.BANKNIFTY,
        ExecutionSide.LONG,
        price,
        _timestamp(minute),
    )


def _close(position_id: str, price: float, minute: int) -> PortfolioCloseEvent:
    """Build one deterministic close event fixture."""
    return PortfolioCloseEvent(position_id, price, _timestamp(minute))


def _timestamp(minutes: int = 0) -> datetime:
    """Return one aware timestamp offset for deterministic ordered events."""
    return datetime(2026, 1, 1, 9, 15, tzinfo=timezone.utc) + timedelta(
        minutes=minutes
    )


class _FailingPolicy:
    """Test-only policy whose failure must cross the orchestration boundary."""

    def allocate(self, request):
        """Fail deliberately without returning an allocation decision."""
        raise RuntimeError("allocation failure")
