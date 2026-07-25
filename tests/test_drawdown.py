"""Contract tests for immutable absolute drawdown analytics."""

import ast
from dataclasses import FrozenInstanceError, is_dataclass
from unittest import TestCase

from src.engines.backtesting import FixedRateTransactionCostModel
from src.engines.execution import ExecutionSide
from src.engines.performance import (
    BasicDrawdownAnalyzer,
    CumulativeEquityCurveBuilder,
    DrawdownAnalyzer,
    DrawdownPoint,
    DrawdownSummary,
    EquityCurve,
    EquityCurveMode,
    RealizedPnLEngine,
    build_drawdown_point,
    build_drawdown_summary,
)

from tests.test_realized_pnl import _trade


class DrawdownTests(TestCase):
    """Verify pure running-peak and absolute-drawdown analysis over equity."""

    def test_empty_curve_has_no_points_and_zero_maximum_drawdown(self) -> None:
        """Represent empty equity without inventing a drawdown point."""
        summary = RealizedPnLEngine().calculate(())
        from src.engines.performance import CumulativeEquityCurveBuilder

        drawdown = BasicDrawdownAnalyzer().analyze(
            CumulativeEquityCurveBuilder().build(summary)
        )

        self.assertIsInstance(drawdown, DrawdownSummary)
        self.assertEqual(drawdown.drawdown_points, ())
        self.assertEqual(drawdown.maximum_drawdown, 0.0)

    def test_monotonic_gains_have_zero_drawdown(self) -> None:
        """Advance running peaks with no decrease from any observed high."""
        summary = _summary_from_pnls((10.0, 20.0))

        curve = _curve_from_summary(summary)
        drawdown = BasicDrawdownAnalyzer().analyze(curve)

        self.assertEqual(
            tuple(point.running_peak for point in drawdown.drawdown_points),
            (10.0, 30.0),
        )
        self.assertEqual(
            tuple(point.drawdown for point in drawdown.drawdown_points),
            (0.0, 0.0),
        )
        self.assertEqual(drawdown.maximum_drawdown, 0.0)

    def test_monotonic_losses_draw_down_from_starting_equity(self) -> None:
        """Keep the zero start as peak while equity remains below it."""
        summary = _summary_from_pnls((-10.0, -10.0))

        drawdown = _analyze(summary)

        self.assertEqual(
            tuple(point.running_peak for point in drawdown.drawdown_points),
            (0.0, 0.0),
        )
        self.assertEqual(
            tuple(point.drawdown for point in drawdown.drawdown_points),
            (10.0, 20.0),
        )
        self.assertEqual(drawdown.maximum_drawdown, 20.0)

    def test_recovery_repeated_peaks_and_flat_equity_preserve_order(self) -> None:
        """Track new peaks, recovery, repeated peaks, and zero changes in order."""
        summary = _summary_from_pnls((10.0, -5.0, 5.0, 0.0, -7.0))

        curve = _curve_from_summary(summary)
        drawdown = BasicDrawdownAnalyzer().analyze(curve)

        self.assertEqual(
            tuple(point.running_peak for point in drawdown.drawdown_points),
            (10.0, 10.0, 10.0, 10.0, 10.0),
        )
        self.assertEqual(
            tuple(point.drawdown for point in drawdown.drawdown_points),
            (0.0, 5.0, 0.0, 0.0, 7.0),
        )
        self.assertEqual(drawdown.maximum_drawdown, 7.0)
        for equity_point, drawdown_point in zip(
            curve.equity_points,
            drawdown.drawdown_points,
            strict=True,
        ):
            self.assertIs(drawdown_point.source_equity_point, equity_point)

    def test_net_curve_uses_existing_net_equity_without_double_cost_subtraction(
        self,
    ) -> None:
        """Analyze a net curve exactly as supplied, with unchanged drawdown rules."""
        trades = (
            _trade(ExecutionSide.LONG, 1, 100.0, 110.0),
            _trade(ExecutionSide.LONG, 1, 100.0, 95.0),
        )
        summary = RealizedPnLEngine(
            FixedRateTransactionCostModel(0.1, 0.0, 0.0, 0.0, 0.0)
        ).calculate(trades)

        gross_drawdown = BasicDrawdownAnalyzer().analyze(
            CumulativeEquityCurveBuilder().build(summary)
        )
        net_curve = CumulativeEquityCurveBuilder(EquityCurveMode.NET).build(summary)
        net_drawdown = BasicDrawdownAnalyzer().analyze(net_curve)

        self.assertEqual(gross_drawdown.maximum_drawdown, 5.0)
        self.assertIs(net_curve.mode, EquityCurveMode.NET)
        self.assertEqual(
            tuple(point.cumulative_realized_pnl for point in net_curve.equity_points),
            (-11.0, -35.5),
        )
        self.assertEqual(
            tuple(point.running_peak for point in net_drawdown.drawdown_points),
            (0.0, 0.0),
        )
        self.assertEqual(
            tuple(point.drawdown for point in net_drawdown.drawdown_points),
            (11.0, 35.5),
        )
        self.assertEqual(net_drawdown.maximum_drawdown, 35.5)

    def test_zero_cost_gross_and_net_curves_have_equal_drawdowns(self) -> None:
        """Preserve equality when existing TradePnL net values equal gross values."""
        summary = RealizedPnLEngine().calculate(
            (
                _trade(ExecutionSide.LONG, 1, 100.0, 110.0),
                _trade(ExecutionSide.LONG, 1, 100.0, 95.0),
            )
        )

        gross = BasicDrawdownAnalyzer().analyze(
            CumulativeEquityCurveBuilder().build(summary)
        )
        net = BasicDrawdownAnalyzer().analyze(
            CumulativeEquityCurveBuilder(EquityCurveMode.NET).build(summary)
        )

        self.assertEqual(gross, net)

    def test_analysis_is_deterministic_and_models_are_immutable(self) -> None:
        """Return equal frozen output without mutating the supplied equity curve."""
        curve = _curve_from_summary(_summary_from_pnls((10.0, -5.0)))
        analyzer: DrawdownAnalyzer = BasicDrawdownAnalyzer()

        first = analyzer.analyze(curve)
        second = analyzer.analyze(curve)

        self.assertEqual(first, second)
        self.assertTrue(is_dataclass(first))
        self.assertTrue(is_dataclass(first.drawdown_points[0]))
        self.assertFalse(hasattr(first, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            first.maximum_drawdown = 0.0
        with self.assertRaises(FrozenInstanceError):
            first.drawdown_points[0].drawdown = 1.0

    def test_builders_and_analyzer_reject_intrinsic_misuse(self) -> None:
        """Require equity points, non-negative drawdowns, and consistent maxima."""
        curve = _curve_from_summary(_summary_from_pnls((10.0,)))
        equity_point = curve.equity_points[0]
        point = build_drawdown_point(equity_point, 10.0, 0.0)

        with self.assertRaises(TypeError):
            BasicDrawdownAnalyzer().analyze(object())
        with self.assertRaises(TypeError):
            build_drawdown_point(object(), 10.0, 0.0)
        with self.assertRaises(ValueError):
            build_drawdown_point(equity_point, 9.0, 0.0)
        with self.assertRaises(ValueError):
            build_drawdown_point(equity_point, 10.0, -1.0)
        with self.assertRaises(TypeError):
            build_drawdown_summary([point])
        with self.assertRaises(ValueError):
            build_drawdown_summary((point,), maximum_drawdown=1.0)
        with self.assertRaises(TypeError):
            DrawdownSummary(drawdown_points=(point,), maximum_drawdown=0)
        with self.assertRaises(TypeError):
            DrawdownPoint(source_equity_point=object(), running_peak=0.0, drawdown=0.0)
        with self.assertRaises(TypeError):
            EquityCurve(equity_points=(), final_equity=0)

    def test_drawdown_modules_depend_only_on_equity_contracts(self) -> None:
        """Keep drawdown analysis independent from portfolio and market layers."""
        expected_imports = {
            "src/engines/performance/drawdown.py": {
                "src.engines.performance.builders",
                "src.engines.performance._drawdown_values",
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


def _summary_from_pnls(realized_pnls: tuple[float, ...]):
    """Build test trades whose explicit realized PnL values match the input tuple."""
    trades = tuple(
        _trade(
            ExecutionSide.LONG,
            1,
            100.0,
            100.0 + realized_pnl,
        )
        for realized_pnl in realized_pnls
    )
    return RealizedPnLEngine().calculate(trades)


def _curve_from_summary(summary):
    """Build a cumulative curve using the existing public construction contract."""
    from src.engines.performance import CumulativeEquityCurveBuilder

    return CumulativeEquityCurveBuilder().build(summary)


def _analyze(summary):
    """Build a curve and analyze it through the public drawdown engine."""
    return BasicDrawdownAnalyzer().analyze(_curve_from_summary(summary))
