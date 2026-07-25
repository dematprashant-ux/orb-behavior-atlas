"""Contract tests for immutable portfolio domain values."""

from dataclasses import FrozenInstanceError, is_dataclass
from datetime import datetime, timezone
from unittest import TestCase

from src.engines.data.models import Instrument
from src.engines.execution import ExecutionSide
from src.engines.portfolio import (
    PortfolioPosition,
    PortfolioSnapshot,
    build_portfolio_position,
    build_portfolio_snapshot,
)


class PortfolioDomainTests(TestCase):
    """Verify local portfolio facts without transitions or valuation."""

    def test_empty_snapshot_is_valid_and_has_no_invested_capital(self) -> None:
        """Represent an empty portfolio without creating a separate aggregate."""
        snapshot = build_portfolio_snapshot(_timestamp(), 1_000.0)

        self.assertEqual(snapshot.positions, ())
        self.assertEqual(snapshot.available_cash, 1_000.0)
        self.assertEqual(snapshot.invested_capital, 0.0)

    def test_positions_preserve_supplied_order_and_entry_capital(self) -> None:
        """Retain position references and determine entry capital only from facts."""
        first = _position("position-1", 2, 100.0)
        second = _position("position-2", 3, 200.0)
        positions = (first, second)

        snapshot = build_portfolio_snapshot(_timestamp(), 200.0, positions)

        self.assertEqual(snapshot.positions, positions)
        self.assertIs(snapshot.positions[0], first)
        self.assertEqual(snapshot.invested_capital, 800.0)

    def test_models_are_immutable_slotted_and_deterministically_equal(self) -> None:
        """Expose immutable value semantics without changing caller collections."""
        position = _position("position-1", 1, 100.0)
        first = build_portfolio_snapshot(_timestamp(), 900.0, (position,))
        second = build_portfolio_snapshot(_timestamp(), 900.0, (position,))

        self.assertEqual(first, second)
        self.assertTrue(is_dataclass(position))
        self.assertTrue(is_dataclass(first))
        self.assertFalse(hasattr(position, "__dict__"))
        self.assertFalse(hasattr(first, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            position.quantity = 2
        with self.assertRaises(FrozenInstanceError):
            first.available_cash = 0.0

    def test_models_reject_invalid_intrinsic_values(self) -> None:
        """Reject invalid cash, quantities, prices, time, and duplicate identities."""
        position = _position("position-1", 1, 100.0)
        with self.assertRaises(ValueError):
            build_portfolio_snapshot(_timestamp(), -1.0)
        with self.assertRaises(ValueError):
            _position("position-1", 0, 100.0)
        with self.assertRaises(ValueError):
            _position("position-1", 1, 0.0)
        with self.assertRaises(ValueError):
            build_portfolio_position(
                "position-1",
                Instrument.BANKNIFTY,
                ExecutionSide.LONG,
                1,
                100.0,
                datetime(2026, 1, 1),
            )
        with self.assertRaises(ValueError):
            build_portfolio_snapshot(_timestamp(), 800.0, (position, position))

    def test_public_exports_reference_canonical_domain_types(self) -> None:
        """Use canonical instrument and side values rather than duplicate enums."""
        position = _position("position-1", 1, 100.0)

        self.assertIs(position.instrument, Instrument.BANKNIFTY)
        self.assertIs(position.side, ExecutionSide.LONG)
        self.assertIsInstance(position, PortfolioPosition)
        self.assertIsInstance(
            build_portfolio_snapshot(_timestamp(), 0.0),
            PortfolioSnapshot,
        )


def _timestamp() -> datetime:
    """Return one explicit aware timestamp for deterministic portfolio fixtures."""
    return datetime(2026, 1, 1, 9, 15, tzinfo=timezone.utc)


def _position(position_id: str, quantity: int, entry_price: float) -> PortfolioPosition:
    """Build one deterministic active-position fixture."""
    return build_portfolio_position(
        position_id,
        Instrument.BANKNIFTY,
        ExecutionSide.LONG,
        quantity,
        entry_price,
        _timestamp(),
    )
