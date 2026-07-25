"""Contract tests for immutable canonical backtest-report composition."""

from dataclasses import FrozenInstanceError, is_dataclass
from unittest import TestCase

from src.engines.execution import ExecutionSide
from src.engines.performance import (
    BacktestReport,
    BasicDrawdownAnalyzer,
    BasicPerformanceAnalyzer,
    BasicRiskMetricsAnalyzer,
    CumulativeEquityCurveBuilder,
    RealizedPnLEngine,
    build_backtest_report,
)

from tests.test_realized_pnl import _trade


class BacktestReportTests(TestCase):
    """Verify report composition retains existing immutable artifacts by reference."""

    def test_successful_composition_preserves_child_references(self) -> None:
        """Build one canonical report without copying or recalculating children."""
        performance, curve, drawdown, risk_metrics = _artifacts()

        report = build_backtest_report(
            performance,
            curve,
            drawdown,
            risk_metrics,
        )

        self.assertIsInstance(report, BacktestReport)
        self.assertIs(report.performance_metrics, performance)
        self.assertIs(report.equity_curve, curve)
        self.assertIs(report.drawdown_summary, drawdown)
        self.assertIs(report.risk_adjusted_metrics, risk_metrics)

    def test_construction_is_deterministic_and_report_is_immutable(self) -> None:
        """Return equal frozen values without changing the supplied artifacts."""
        artifacts = _artifacts()

        first = build_backtest_report(*artifacts)
        second = build_backtest_report(*artifacts)

        self.assertEqual(first, second)
        self.assertTrue(is_dataclass(first))
        self.assertFalse(hasattr(first, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            first.equity_curve = artifacts[1]

    def test_builder_rejects_only_invalid_child_artifact_types(self) -> None:
        """Require the four existing immutable artifact models for composition."""
        performance, curve, drawdown, risk_metrics = _artifacts()

        with self.assertRaises(TypeError):
            build_backtest_report(object(), curve, drawdown, risk_metrics)
        with self.assertRaises(TypeError):
            build_backtest_report(performance, object(), drawdown, risk_metrics)
        with self.assertRaises(TypeError):
            build_backtest_report(performance, curve, object(), risk_metrics)
        with self.assertRaises(TypeError):
            build_backtest_report(performance, curve, drawdown, object())


def _artifacts():
    """Build compatible immutable analytics artifacts through public contracts."""
    trades = (
        _trade(ExecutionSide.LONG, 1, 100.0, 110.0),
        _trade(ExecutionSide.LONG, 1, 100.0, 95.0),
    )
    summary = RealizedPnLEngine().calculate(trades)
    performance = BasicPerformanceAnalyzer().analyze(summary)
    curve = CumulativeEquityCurveBuilder().build(summary)
    drawdown = BasicDrawdownAnalyzer().analyze(curve)
    risk_metrics = BasicRiskMetricsAnalyzer().analyze(performance, drawdown)
    return performance, curve, drawdown, risk_metrics
