"""Contract tests for portfolio-equity performance and shared drawdown facts."""

from dataclasses import FrozenInstanceError, is_dataclass
from datetime import datetime, timedelta, timezone
from unittest import TestCase

from src.engines.portfolio import (
    PortfolioDrawdownAnalyzer,
    PortfolioPerformanceAnalyzer,
    StandardPortfolioDrawdownAnalyzer,
    StandardPortfolioEquityCurveBuilder,
    StandardPortfolioPerformanceAnalyzer,
    build_portfolio_equity_point,
    build_portfolio_equity_curve,
    build_portfolio_performance_metrics,
    build_portfolio_snapshot,
)


class PortfolioPerformanceMetricsTests(TestCase):
    """Verify pure portfolio-equity analysis without trade-level statistics."""

    def test_empty_curve_uses_explicit_zero_safe_metrics_and_drawdown(self) -> None:
        """Represent no portfolio observations without inventing a return ratio."""
        curve = StandardPortfolioEquityCurveBuilder().build(())
        metrics = StandardPortfolioPerformanceAnalyzer().analyze(curve)
        drawdown = StandardPortfolioDrawdownAnalyzer().analyze(curve)

        self.assertEqual(metrics.initial_equity, 0.0)
        self.assertEqual(metrics.final_equity, 0.0)
        self.assertEqual(metrics.absolute_return, 0.0)
        self.assertIsNone(metrics.total_return)
        self.assertEqual(metrics.maximum_equity, 0.0)
        self.assertEqual(metrics.minimum_equity, 0.0)
        self.assertEqual(metrics.equity_point_count, 0)
        self.assertEqual(drawdown.drawdown_points, ())
        self.assertEqual(drawdown.maximum_drawdown, 0.0)

    def test_single_unchanged_profitable_and_losing_equity_are_exact(self) -> None:
        """Calculate return facts only from the selected ordered curve values."""
        unchanged = _curve((100.0,))
        profitable = _curve((100.0, 125.0, 120.0))
        losing = _curve((100.0, 75.0))

        self.assertEqual(
            StandardPortfolioPerformanceAnalyzer().analyze(unchanged).total_return,
            0.0,
        )
        metrics = StandardPortfolioPerformanceAnalyzer().analyze(profitable)
        self.assertEqual(metrics.absolute_return, 20.0)
        self.assertEqual(metrics.total_return, 0.2)
        self.assertEqual(metrics.maximum_equity, 125.0)
        self.assertEqual(metrics.minimum_equity, 100.0)
        self.assertEqual(metrics.equity_point_count, 3)
        self.assertEqual(
            StandardPortfolioPerformanceAnalyzer().analyze(losing).absolute_return,
            -25.0,
        )

    def test_portfolio_drawdown_reuses_shared_absolute_drawdown_formula(self) -> None:
        """Use running peaks from zero and preserve portfolio equity references."""
        curve = _curve((100.0, 125.0, 110.0, 130.0))
        summary: PortfolioDrawdownAnalyzer = StandardPortfolioDrawdownAnalyzer()
        drawdown = summary.analyze(curve)

        self.assertEqual(
            tuple(point.running_peak for point in drawdown.drawdown_points),
            (100.0, 125.0, 125.0, 130.0),
        )
        self.assertEqual(
            tuple(point.drawdown for point in drawdown.drawdown_points),
            (0.0, 0.0, 15.0, 0.0),
        )
        self.assertEqual(drawdown.maximum_drawdown, 15.0)
        self.assertIs(drawdown.drawdown_points[2].source_equity_point, curve.equity_points[2])

    def test_results_are_immutable_deterministic_and_protocol_compatible(self) -> None:
        """Expose stable output without inspecting positions or mutating the curve."""
        curve = _curve((100.0, 110.0))
        analyzer: PortfolioPerformanceAnalyzer = StandardPortfolioPerformanceAnalyzer()
        first = analyzer.analyze(curve)
        second = analyzer.analyze(curve)

        self.assertEqual(first, second)
        self.assertTrue(is_dataclass(first))
        self.assertFalse(hasattr(first, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            first.final_equity = 0.0

    def test_boundary_rejects_intrinsic_misuse_without_lower_layer_revalidation(self) -> None:
        """Require curve types and metric relationships while accepting zero equity."""
        with self.assertRaises(TypeError):
            StandardPortfolioPerformanceAnalyzer().analyze(object())
        with self.assertRaises(TypeError):
            StandardPortfolioDrawdownAnalyzer().analyze(object())
        with self.assertRaises(ValueError):
            build_portfolio_performance_metrics(
                100.0, 110.0, 10.0, 0.2, 110.0, 100.0, 2
            )
        metrics = build_portfolio_performance_metrics(
            0.0, 0.0, 0.0, None, 0.0, 0.0, 0
        )
        self.assertIsNone(metrics.total_return)


def _curve(values: tuple[float, ...]):
    """Build a deterministic portfolio equity curve directly from point values."""
    points = tuple(
        build_portfolio_equity_point(_timestamp(index), value, 0.0)
        for index, value in enumerate(values)
    )
    return build_portfolio_equity_curve(points)


def _timestamp(minutes: int) -> datetime:
    """Return one explicit aware timestamp for ordered equity fixtures."""
    return datetime(2026, 1, 1, 9, 15, tzinfo=timezone.utc) + timedelta(
        minutes=minutes
    )
