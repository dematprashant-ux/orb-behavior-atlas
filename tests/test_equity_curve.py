"""Contract tests for immutable cumulative realized-equity artifacts."""

import ast
from dataclasses import FrozenInstanceError, is_dataclass
from unittest import TestCase

from src.engines.execution import ExecutionSide
from src.engines.performance import (
    CumulativeEquityCurveBuilder,
    EquityCurve,
    EquityCurveBuilder,
    EquityCurveMode,
    EquityPoint,
    RealizedPnLEngine,
    build_equity_curve,
    build_equity_point,
)

from tests.test_realized_pnl import _trade


class EquityCurveTests(TestCase):
    """Verify pure ordered accumulation without drawdown or portfolio analysis."""

    def test_empty_summary_has_no_points_and_zero_final_equity(self) -> None:
        """Start at zero without fabricating a point for an empty PnL summary."""
        curve = _build_curve(())

        self.assertIsInstance(curve, EquityCurve)
        self.assertEqual(curve.equity_points, ())
        self.assertEqual(curve.final_equity, 0.0)

    def test_single_positive_trade_creates_one_cumulative_point(self) -> None:
        """Accumulate one supplied realized-PnL value from zero starting equity."""
        curve = _build_curve((_trade(ExecutionSide.LONG, 1, 100.0, 110.0),))

        self.assertEqual(len(curve.equity_points), 1)
        self.assertEqual(curve.equity_points[0].cumulative_realized_pnl, 10.0)
        self.assertEqual(curve.final_equity, 10.0)
        self.assertIs(curve.mode, EquityCurveMode.GROSS)

    def test_net_mode_accumulates_existing_net_pnl_without_recalculation(self) -> None:
        """Select net facts while preserving canonical PnL order and references."""
        trades = (
            _trade(ExecutionSide.LONG, 1, 100.0, 110.0),
            _trade(ExecutionSide.LONG, 1, 100.0, 90.0),
        )
        summary = RealizedPnLEngine(
            _FixedCostModel(2.0)
        ).calculate(trades)

        curve = CumulativeEquityCurveBuilder(EquityCurveMode.NET).build(summary)

        self.assertIs(curve.mode, EquityCurveMode.NET)
        self.assertEqual(
            tuple(point.cumulative_realized_pnl for point in curve.equity_points),
            (8.0, -4.0),
        )
        self.assertEqual(curve.final_equity, -4.0)
        for trade_pnl, point in zip(
            summary.trade_pnls,
            curve.equity_points,
            strict=True,
        ):
            self.assertIs(point.source_trade_pnl, trade_pnl)

    def test_zero_cost_gross_and_net_curves_are_equal(self) -> None:
        """Retain identical curves when each existing trade has zero cost."""
        summary = RealizedPnLEngine().calculate(
            (_trade(ExecutionSide.LONG, 1, 100.0, 110.0),)
        )

        gross = CumulativeEquityCurveBuilder().build(summary)
        net = CumulativeEquityCurveBuilder(EquityCurveMode.NET).build(summary)

        self.assertEqual(gross.final_equity, net.final_equity)
        self.assertEqual(
            tuple(point.cumulative_realized_pnl for point in gross.equity_points),
            tuple(point.cumulative_realized_pnl for point in net.equity_points),
        )

    def test_accumulates_profitable_losing_mixed_and_zero_pnl_in_order(self) -> None:
        """Preserve exact source order while adding each existing realized PnL once."""
        trades = (
            _trade(ExecutionSide.LONG, 1, 100.0, 110.0),
            _trade(ExecutionSide.LONG, 1, 100.0, 95.0),
            _trade(ExecutionSide.SHORT, 1, 100.0, 100.0),
            _trade(ExecutionSide.SHORT, 1, 110.0, 100.0),
        )
        summary = RealizedPnLEngine().calculate(trades)

        curve = CumulativeEquityCurveBuilder().build(summary)

        self.assertEqual(
            tuple(point.cumulative_realized_pnl for point in curve.equity_points),
            (10.0, 5.0, 5.0, 15.0),
        )
        self.assertEqual(curve.final_equity, 15.0)
        for trade_pnl, point in zip(
            summary.trade_pnls,
            curve.equity_points,
            strict=True,
        ):
            self.assertIs(point.source_trade_pnl, trade_pnl)

    def test_curve_construction_is_deterministic_and_models_are_immutable(self) -> None:
        """Return equal frozen curves without mutating immutable PnL inputs."""
        summary = RealizedPnLEngine().calculate(
            (_trade(ExecutionSide.LONG, 2, 100.0, 105.0),)
        )
        builder: EquityCurveBuilder = CumulativeEquityCurveBuilder()

        first = builder.build(summary)
        second = builder.build(summary)

        self.assertEqual(first, second)
        self.assertTrue(is_dataclass(first))
        self.assertTrue(is_dataclass(first.equity_points[0]))
        self.assertFalse(hasattr(first, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            first.final_equity = 0.0
        with self.assertRaises(FrozenInstanceError):
            first.equity_points[0].cumulative_realized_pnl = 0.0

    def test_builders_and_engine_reject_intrinsic_misuse(self) -> None:
        """Require immutable PnL summaries, points, finite values, and totals."""
        summary = RealizedPnLEngine().calculate(
            (_trade(ExecutionSide.LONG, 1, 100.0, 110.0),)
        )
        point = build_equity_point(summary.trade_pnls[0], 10.0)

        with self.assertRaises(TypeError):
            CumulativeEquityCurveBuilder().build(object())
        with self.assertRaises(TypeError):
            CumulativeEquityCurveBuilder("NET")
        with self.assertRaises(TypeError):
            build_equity_point(object(), 10.0)
        with self.assertRaises(TypeError):
            build_equity_point(summary.trade_pnls[0], 10)
        with self.assertRaises(TypeError):
            build_equity_curve([point])
        with self.assertRaises(ValueError):
            build_equity_curve((point,), final_equity=9.0)
        with self.assertRaises(TypeError):
            EquityCurve(equity_points=(point,), final_equity=10)
        with self.assertRaises(TypeError):
            EquityPoint(source_trade_pnl=object(), cumulative_realized_pnl=10.0)

    def test_equity_modules_depend_only_on_pnl_contracts(self) -> None:
        """Keep cumulative construction independent from portfolio analytics and I/O."""
        expected_imports = {
            "src/engines/performance/equity.py": {
                "dataclasses",
                "src.engines.performance.builders",
                "src.engines.performance.models",
            },
            "src/engines/performance/interfaces.py": {
                "collections.abc",
                "pathlib",
                "typing",
                "src.engines.execution.models",
                "src.engines.performance.models",
            },
        }

        for path, expected in expected_imports.items():
            with self.subTest(path=path), open(path, encoding="utf-8") as source_file:
                tree = ast.parse(source_file.read())
            imported_modules = {
                node.module
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.module is not None
            }
            self.assertEqual(imported_modules, expected)


def _build_curve(trades):
    """Build an immutable PnL summary and cumulative curve from test trades."""
    summary = RealizedPnLEngine().calculate(trades)
    return CumulativeEquityCurveBuilder().build(summary)


class _FixedCostModel:
    """Test-only deterministic cost model that returns a supplied total cost."""

    def __init__(self, total_cost: float) -> None:
        """Retain one explicit cost for every test trade."""
        self._total_cost = total_cost

    def calculate(
        self,
        *,
        entry_price: float,
        exit_price: float,
        quantity: int,
    ):
        """Return an existing boundary-shaped object without inspecting trade facts."""
        return _CostBreakdown(self._total_cost)


class _CostBreakdown:
    """Test-only object exposing the cost property required by the PnL engine."""

    def __init__(self, total_cost: float) -> None:
        """Store the explicit test cost without mutable behavior."""
        self.total_cost = total_cost
