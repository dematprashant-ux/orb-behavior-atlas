"""Contract tests for zero-safe risk-adjusted performance metrics."""

import ast
from dataclasses import FrozenInstanceError, is_dataclass
from math import inf
from unittest import TestCase

from src.engines.execution import ExecutionSide
from src.engines.performance import (
    BasicDrawdownAnalyzer,
    BasicPerformanceAnalyzer,
    BasicRiskMetricsAnalyzer,
    CumulativeEquityCurveBuilder,
    RealizedPnLEngine,
    RiskAdjustedMetrics,
    RiskMetricsAnalyzer,
    build_risk_adjusted_metrics,
)

from tests.test_realized_pnl import _trade


class RiskMetricsTests(TestCase):
    """Verify pure absolute-return-to-drawdown metric analysis."""

    def test_positive_negative_and_zero_net_profit(self) -> None:
        """Calculate matching finite ratios without classifying the results."""
        positive = _analyze((10.0, -5.0))
        negative = _analyze((-10.0,))
        zero = _analyze((10.0, -10.0))

        self.assertEqual(
            (positive.recovery_factor, positive.return_over_drawdown),
            (1.0, 1.0),
        )
        self.assertEqual(
            (negative.recovery_factor, negative.return_over_drawdown),
            (-1.0, -1.0),
        )
        self.assertEqual(
            (zero.recovery_factor, zero.return_over_drawdown),
            (0.0, 0.0),
        )

    def test_zero_drawdown_and_empty_artifacts_return_none(self) -> None:
        """Avoid division by zero and never fabricate infinite metric values."""
        gains_only = _analyze((10.0,))
        empty = _analyze(())

        self.assertEqual(
            (gains_only.recovery_factor, gains_only.return_over_drawdown),
            (None, None),
        )
        self.assertEqual(
            (empty.recovery_factor, empty.return_over_drawdown),
            (None, None),
        )

    def test_analysis_is_deterministic_and_output_is_immutable(self) -> None:
        """Return equal frozen models without changing supplied source artifacts."""
        performance, drawdown = _artifacts((10.0, -5.0))
        analyzer: RiskMetricsAnalyzer = BasicRiskMetricsAnalyzer()

        first = analyzer.analyze(performance, drawdown)
        second = analyzer.analyze(performance, drawdown)

        self.assertEqual(first, second)
        self.assertTrue(is_dataclass(first))
        self.assertFalse(hasattr(first, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            first.recovery_factor = 0.0

    def test_builder_and_analyzer_reject_intrinsic_misuse(self) -> None:
        """Require source model types and matching finite ratio values."""
        performance, drawdown = _artifacts((10.0, -5.0))

        with self.assertRaises(TypeError):
            BasicRiskMetricsAnalyzer().analyze(object(), drawdown)
        with self.assertRaises(TypeError):
            BasicRiskMetricsAnalyzer().analyze(performance, object())
        with self.assertRaises(TypeError):
            build_risk_adjusted_metrics(1, 1.0)
        with self.assertRaises(ValueError):
            build_risk_adjusted_metrics(inf, inf)
        with self.assertRaises(ValueError):
            build_risk_adjusted_metrics(1.0, 2.0)

    def test_risk_metrics_depend_only_on_aggregate_contracts(self) -> None:
        """Keep risk metrics independent from execution and market layers."""
        with open("src/engines/performance/risk.py", encoding="utf-8") as source_file:
            tree = ast.parse(source_file.read())

        imported_modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        self.assertEqual(
            imported_modules,
            {
                "math",
                "src.engines.performance.builders",
                "src.engines.performance.models",
            },
        )


def _analyze(realized_pnls: tuple[float, ...]) -> RiskAdjustedMetrics:
    """Build aggregate artifacts and analyze them through public contracts."""
    performance, drawdown = _artifacts(realized_pnls)
    return BasicRiskMetricsAnalyzer().analyze(performance, drawdown)


def _artifacts(realized_pnls: tuple[float, ...]):
    """Build immutable metrics and drawdown artifacts from test-only trades."""
    trades = tuple(
        _trade(ExecutionSide.LONG, 1, 100.0, 100.0 + realized_pnl)
        for realized_pnl in realized_pnls
    )
    summary = RealizedPnLEngine().calculate(trades)
    performance = BasicPerformanceAnalyzer().analyze(summary)
    curve = CumulativeEquityCurveBuilder().build(summary)
    drawdown = BasicDrawdownAnalyzer().analyze(curve)
    return performance, drawdown
