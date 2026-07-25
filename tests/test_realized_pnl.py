"""Contract tests for deterministic realized PnL from completed trades."""

import ast
from dataclasses import FrozenInstanceError, is_dataclass
from math import inf
from unittest import TestCase

from src.engines.execution import CompletedTrade, ExecutionSide, build_completed_trade
from src.engines.performance import (
    PnLEngine,
    PnLSummary,
    RealizedPnLEngine,
    TradePnL,
    build_pnl_summary,
    build_trade_pnl,
)

from tests.test_completed_trade_execution import _accepted_result


class RealizedPnLEngineTests(TestCase):
    """Verify deterministic non-cost realized PnL from explicit trade facts."""

    def test_calculates_profitable_losing_and_zero_long_pnl(self) -> None:
        """Apply the long formula without rounding or profitability labels."""
        trades = (
            _trade(ExecutionSide.LONG, 2, 100.0, 110.0),
            _trade(ExecutionSide.LONG, 3, 100.0, 90.0),
            _trade(ExecutionSide.LONG, 4, 100.0, 100.0),
        )

        summary = RealizedPnLEngine().calculate(trades)

        self.assertEqual(
            tuple(trade_pnl.realized_pnl for trade_pnl in summary.trade_pnls),
            (20.0, -30.0, 0.0),
        )
        self.assertEqual(summary.total_realized_pnl, -10.0)

    def test_calculates_profitable_losing_and_zero_short_pnl(self) -> None:
        """Apply the short formula without using a contract multiplier or lot size."""
        trades = (
            _trade(ExecutionSide.SHORT, 2, 110.0, 100.0),
            _trade(ExecutionSide.SHORT, 3, 90.0, 100.0),
            _trade(ExecutionSide.SHORT, 4, 100.0, 100.0),
        )

        summary = RealizedPnLEngine().calculate(trades)

        self.assertEqual(
            tuple(trade_pnl.realized_pnl for trade_pnl in summary.trade_pnls),
            (20.0, -30.0, 0.0),
        )
        self.assertEqual(summary.total_realized_pnl, -10.0)

    def test_preserves_order_and_child_references_for_mixed_trade_sides(self) -> None:
        """Produce one ordered PnL item per existing completed trade."""
        trades = (
            _trade(ExecutionSide.SHORT, 1, 110.0, 100.0),
            _trade(ExecutionSide.LONG, 2, 100.0, 105.0),
        )

        summary = RealizedPnLEngine().calculate(trades)

        self.assertIsInstance(summary, PnLSummary)
        self.assertIsInstance(summary.trade_pnls, tuple)
        self.assertEqual(summary.total_realized_pnl, 20.0)
        for trade, trade_pnl in zip(trades, summary.trade_pnls, strict=True):
            self.assertIs(trade_pnl.source_completed_trade, trade)

    def test_empty_trade_input_returns_zero_total(self) -> None:
        """Represent no supplied completed trades without fabricating results."""
        summary = RealizedPnLEngine().calculate(())

        self.assertEqual(summary.trade_pnls, ())
        self.assertEqual(summary.total_realized_pnl, 0)

    def test_calculation_is_deterministic_and_models_are_immutable(self) -> None:
        """Return equal frozen values without mutating supplied completed trades."""
        trade = _trade(ExecutionSide.LONG, 2, 100.0, 105.0)
        engine: PnLEngine = RealizedPnLEngine()

        first = engine.calculate((trade,))
        second = engine.calculate((trade,))

        self.assertEqual(first, second)
        self.assertTrue(is_dataclass(first))
        self.assertTrue(is_dataclass(first.trade_pnls[0]))
        self.assertFalse(hasattr(first, "__dict__"))
        self.assertIs(first.trade_pnls[0].source_completed_trade, trade)
        with self.assertRaises(FrozenInstanceError):
            first.total_realized_pnl = 0.0
        with self.assertRaises(FrozenInstanceError):
            first.trade_pnls[0].realized_pnl = 0.0

    def test_builders_and_engine_reject_intrinsic_misuse(self) -> None:
        """Require explicit completed trades, finite PnLs, and consistent totals."""
        trade = _trade(ExecutionSide.LONG, 1, 100.0, 110.0)
        trade_pnl = build_trade_pnl(trade, 10.0)

        with self.assertRaises(TypeError):
            RealizedPnLEngine().calculate([])
        with self.assertRaises(TypeError):
            RealizedPnLEngine().calculate((object(),))
        with self.assertRaises(TypeError):
            build_trade_pnl(object(), 10.0)
        with self.assertRaises(ValueError):
            build_trade_pnl(trade, 9.0)
        with self.assertRaises(ValueError):
            build_trade_pnl(trade, inf)
        with self.assertRaises(TypeError):
            build_pnl_summary([trade_pnl])
        with self.assertRaises(TypeError):
            build_pnl_summary((object(),))
        with self.assertRaises(ValueError):
            build_pnl_summary((trade_pnl,), total_realized_pnl=9.0)
        with self.assertRaises(TypeError):
            PnLSummary(trade_pnls=(trade_pnl,), total_realized_pnl=10)

    def test_pnl_modules_depend_only_on_completed_trade_contracts(self) -> None:
        """Keep calculations independent from candles, fills, and infrastructure."""
        expected_imports = {
            "src/engines/performance/pnl.py": {
                "src.engines.execution.models",
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


def _trade(
    side: ExecutionSide,
    quantity: int,
    entry_price: float,
    exit_price: float,
) -> CompletedTrade:
    """Build one explicit immutable closed trade for realized-PnL tests."""
    return build_completed_trade(
        _accepted_result(),
        side,
        quantity,
        entry_price,
        exit_price,
    )
