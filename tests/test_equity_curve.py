"""Contract tests for immutable cumulative realized-equity artifacts."""

import ast
from dataclasses import FrozenInstanceError, is_dataclass
from unittest import TestCase

from src.engines.execution import ExecutionSide
from src.engines.performance import (
    CumulativeEquityCurveBuilder,
    EquityCurve,
    EquityCurveBuilder,
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
        for trade_pnl, point in zip(summary.trade_pnls, curve.equity_points, strict=True):
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
                "src.engines.performance.builders",
                "src.engines.performance.models",
            },
            "src/engines/performance/interfaces.py": {
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
