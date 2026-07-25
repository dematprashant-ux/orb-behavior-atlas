"""Contract tests for deterministic aggregate trading performance metrics."""

import ast
from dataclasses import FrozenInstanceError, replace
from unittest import TestCase

from src.engines.execution import ExecutionSide
from src.engines.performance import (
    BasicPerformanceAnalyzer,
    PerformanceAnalyzer,
    PerformanceMetrics,
    RealizedPnLEngine,
    build_performance_metrics,
)

from tests.test_realized_pnl import _trade


class PerformanceMetricsTests(TestCase):
    """Verify unrounded deterministic statistics over immutable PnL summaries."""

    def test_empty_summary_uses_documented_zero_safe_values(self) -> None:
        """Avoid division and infinities when no realized trades are supplied."""
        metrics = _analyze(())

        self.assertEqual(metrics.total_trades, 0)
        self.assertEqual(
            (metrics.winning_trades, metrics.losing_trades, metrics.flat_trades),
            (0, 0, 0),
        )
        self.assertEqual(
            (metrics.win_rate, metrics.loss_rate, metrics.flat_rate),
            (0.0, 0.0, 0.0),
        )
        self.assertEqual(
            (
                metrics.average_trade_pnl,
                metrics.average_winning_trade,
                metrics.average_losing_trade,
                metrics.expectancy,
            ),
            (0.0, 0.0, 0.0, 0.0),
        )
        self.assertIsNone(metrics.profit_factor)

    def test_single_winning_losing_and_flat_trade_metrics(self) -> None:
        """Classify positive, negative, and zero PnL without extra labels."""
        winner = _analyze((_trade(ExecutionSide.LONG, 1, 100.0, 110.0),))
        loser = _analyze((_trade(ExecutionSide.LONG, 1, 100.0, 90.0),))
        flat = _analyze((_trade(ExecutionSide.LONG, 1, 100.0, 100.0),))

        self.assertEqual((winner.winning_trades, winner.gross_profit), (1, 10.0))
        self.assertIsNone(winner.profit_factor)
        self.assertEqual((loser.losing_trades, loser.gross_loss), (1, 10.0))
        self.assertEqual(loser.average_losing_trade, -10.0)
        self.assertEqual((flat.flat_trades, flat.net_profit), (1, 0.0))

    def test_mixed_summary_calculates_counts_rates_averages_and_profit_factor(self) -> None:
        """Use only realized PnL values for all required aggregate metrics."""
        metrics = _analyze(
            (
                _trade(ExecutionSide.LONG, 1, 100.0, 110.0),
                _trade(ExecutionSide.SHORT, 2, 110.0, 100.0),
                _trade(ExecutionSide.LONG, 1, 100.0, 95.0),
                _trade(ExecutionSide.SHORT, 1, 100.0, 100.0),
            )
        )

        self.assertEqual(metrics.total_trades, 4)
        self.assertEqual(
            (metrics.winning_trades, metrics.losing_trades, metrics.flat_trades),
            (2, 1, 1),
        )
        self.assertEqual((metrics.gross_profit, metrics.gross_loss), (30.0, 5.0))
        self.assertEqual(metrics.net_profit, 25.0)
        self.assertEqual((metrics.win_rate, metrics.loss_rate, metrics.flat_rate), (0.5, 0.25, 0.25))
        self.assertEqual(metrics.average_trade_pnl, 6.25)
        self.assertEqual(metrics.average_winning_trade, 15.0)
        self.assertEqual(metrics.average_losing_trade, -5.0)
        self.assertEqual(metrics.profit_factor, 6.0)
        self.assertEqual(metrics.expectancy, 6.25)

    def test_all_winners_losers_and_flat_results_are_supported(self) -> None:
        """Preserve valid degenerate portfolios without division-by-zero artifacts."""
        all_winners = _analyze(
            (
                _trade(ExecutionSide.LONG, 1, 100.0, 105.0),
                _trade(ExecutionSide.LONG, 1, 100.0, 110.0),
            )
        )
        all_losers = _analyze(
            (
                _trade(ExecutionSide.LONG, 1, 100.0, 95.0),
                _trade(ExecutionSide.LONG, 1, 100.0, 90.0),
            )
        )
        all_flat = _analyze(
            (
                _trade(ExecutionSide.LONG, 1, 100.0, 100.0),
                _trade(ExecutionSide.SHORT, 1, 100.0, 100.0),
            )
        )

        self.assertIsNone(all_winners.profit_factor)
        self.assertEqual(all_losers.profit_factor, 0.0)
        self.assertIsNone(all_flat.profit_factor)
        self.assertEqual(all_flat.flat_rate, 1.0)

    def test_analysis_is_deterministic_and_metrics_are_immutable(self) -> None:
        """Return equal frozen metrics without mutating the source PnL summary."""
        summary = RealizedPnLEngine().calculate(
            (_trade(ExecutionSide.LONG, 1, 100.0, 110.0),)
        )
        analyzer: PerformanceAnalyzer = BasicPerformanceAnalyzer()

        first = analyzer.analyze(summary)
        second = analyzer.analyze(summary)

        self.assertEqual(first, second)
        self.assertFalse(hasattr(first, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            first.net_profit = 0.0

    def test_builder_and_analyzer_reject_intrinsic_misuse(self) -> None:
        """Require a summary and internally consistent metric values."""
        metrics = _analyze((_trade(ExecutionSide.LONG, 1, 100.0, 110.0),))

        with self.assertRaises(TypeError):
            BasicPerformanceAnalyzer().analyze(object())
        with self.assertRaises(ValueError):
            replace(metrics, total_trades=-1)
        with self.assertRaises(ValueError):
            replace(metrics, winning_trades=0)
        with self.assertRaises(TypeError):
            replace(metrics, profit_factor=True)
        with self.assertRaises(ValueError):
            build_performance_metrics(
                total_trades=1,
                winning_trades=1,
                losing_trades=0,
                flat_trades=0,
                gross_profit=10.0,
                gross_loss=0.0,
                net_profit=10.0,
                win_rate=1.0,
                loss_rate=0.0,
                flat_rate=0.0,
                average_trade_pnl=10.0,
                average_winning_trade=10.0,
                average_losing_trade=0.0,
                profit_factor=1.0,
                expectancy=10.0,
            )

    def test_metrics_modules_depend_only_on_pnl_contracts(self) -> None:
        """Keep metrics independent from market, execution, and portfolio layers."""
        with open(
            "src/engines/performance/metrics.py",
            encoding="utf-8",
        ) as source_file:
            tree = ast.parse(source_file.read())

        imported_modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        self.assertEqual(
            imported_modules,
            {
                "src.engines.performance.builders",
                "src.engines.performance.models",
            },
        )


def _analyze(trades):
    """Build a PnL summary and analyze it through the public concrete engine."""
    return BasicPerformanceAnalyzer().analyze(RealizedPnLEngine().calculate(trades))
