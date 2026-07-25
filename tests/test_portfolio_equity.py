"""Contract tests for immutable portfolio equity under injected valuation."""

from dataclasses import FrozenInstanceError, is_dataclass
from datetime import datetime, timedelta, timezone
from unittest import TestCase

from src.engines.data.models import Instrument
from src.engines.execution import ExecutionSide
from src.engines.portfolio import (
    CostBasisPortfolioValuation,
    PortfolioEquityCurve,
    PortfolioEquityCurveBuilder,
    StandardPortfolioEquityCurveBuilder,
    build_portfolio_equity_curve,
    build_portfolio_equity_point,
    build_portfolio_position,
    build_portfolio_snapshot,
)


class PortfolioEquityTests(TestCase):
    """Verify cash plus explicit open-position valuation without analytics."""

    def test_empty_curve_is_valid_with_zero_final_equity(self) -> None:
        """Do not fabricate an initial point when no snapshots are supplied."""
        curve = StandardPortfolioEquityCurveBuilder().build(())

        self.assertEqual(curve.equity_points, ())
        self.assertEqual(curve.final_equity, 0.0)

    def test_cost_basis_curve_combines_cash_and_active_entry_capital(self) -> None:
        """Value an open position once without double-counting deducted cash."""
        snapshots = (
            _snapshot(0, 1_000.0),
            _snapshot(1, 800.0, (_position(),)),
            _snapshot(2, 1_020.0),
        )

        curve = StandardPortfolioEquityCurveBuilder().build(snapshots)

        self.assertEqual(
            tuple(point.total_equity for point in curve.equity_points),
            (1_000.0, 1_000.0, 1_020.0),
        )
        self.assertEqual(curve.equity_points[1].position_value, 200.0)
        self.assertEqual(curve.final_equity, 1_020.0)

    def test_injected_valuation_can_change_open_position_value_explicitly(self) -> None:
        """Use supplied valuation facts while preserving snapshots and ordering."""
        snapshot = _snapshot(1, 800.0, (_position(),))
        builder: PortfolioEquityCurveBuilder = StandardPortfolioEquityCurveBuilder(
            _FixedValuation(350.0)
        )

        curve = builder.build((snapshot,))

        self.assertEqual(curve.equity_points[0].position_value, 350.0)
        self.assertEqual(curve.final_equity, 1_150.0)
        self.assertEqual(snapshot.invested_capital, 200.0)

    def test_models_are_immutable_deterministic_and_preserve_order(self) -> None:
        """Keep caller-supplied snapshot order without valuation side effects."""
        snapshots = (_snapshot(2, 1_000.0), _snapshot(1, 900.0))
        builder = StandardPortfolioEquityCurveBuilder(CostBasisPortfolioValuation())
        first = builder.build(snapshots)
        second = builder.build(snapshots)

        self.assertEqual(first, second)
        self.assertEqual(
            tuple(point.timestamp for point in first.equity_points),
            tuple(snapshot.timestamp for snapshot in snapshots),
        )
        self.assertTrue(is_dataclass(first))
        self.assertFalse(hasattr(first, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            first.final_equity = 0.0

    def test_boundary_rejects_intrinsic_misuse_and_propagates_policy_failure(self) -> None:
        """Reject malformed values but do not suppress valuation failures."""
        point = build_portfolio_equity_point(_timestamp(), 1_000.0, 0.0)
        with self.assertRaises(TypeError):
            StandardPortfolioEquityCurveBuilder().build([])
        with self.assertRaises(TypeError):
            StandardPortfolioEquityCurveBuilder(None)
        with self.assertRaises(TypeError):
            build_portfolio_equity_curve([point])
        with self.assertRaises(ValueError):
            build_portfolio_equity_curve((point,), final_equity=1.0)
        with self.assertRaises(ValueError):
            StandardPortfolioEquityCurveBuilder(_FixedValuation(-1.0)).build(
                (_snapshot(0, 1_000.0),)
            )
        with self.assertRaises(RuntimeError):
            StandardPortfolioEquityCurveBuilder(_FailingValuation()).build(
                (_snapshot(0, 1_000.0),)
            )
        self.assertIsInstance(
            build_portfolio_equity_curve((point,)),
            PortfolioEquityCurve,
        )


def _snapshot(minute: int, cash: float, positions=()):
    """Build one deterministic immutable portfolio snapshot fixture."""
    return build_portfolio_snapshot(_timestamp(minute), cash, positions)


def _position():
    """Build one explicit active position costing two hundred currency units."""
    return build_portfolio_position(
        "one",
        Instrument.BANKNIFTY,
        ExecutionSide.LONG,
        2,
        100.0,
        _timestamp(1),
    )


def _timestamp(minutes: int = 0) -> datetime:
    """Return an aware timestamp for deterministic portfolio equity fixtures."""
    return datetime(2026, 1, 1, 9, 15, tzinfo=timezone.utc) + timedelta(
        minutes=minutes
    )


class _FixedValuation:
    """Test-only explicit valuation policy with no market-data access."""

    def __init__(self, value: float) -> None:
        """Retain the explicit position value returned for every snapshot."""
        self._value = value

    def value(self, snapshot):
        """Return one supplied value without inspecting or modifying snapshot data."""
        return self._value


class _FailingValuation:
    """Test-only policy whose failure must propagate unchanged."""

    def value(self, snapshot):
        """Fail deliberately without returning a valuation result."""
        raise RuntimeError("valuation failure")
