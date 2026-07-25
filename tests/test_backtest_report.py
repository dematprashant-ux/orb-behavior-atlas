"""Contract tests for immutable canonical backtest-report composition."""

from dataclasses import FrozenInstanceError, is_dataclass, replace
from unittest import TestCase

from src.engines.backtesting import FixedRateTransactionCostModel
from src.engines.execution import ExecutionSide
from src.engines.performance import (
    BacktestReport,
    BasicDrawdownAnalyzer,
    BasicPerformanceAnalyzer,
    BasicRiskMetricsAnalyzer,
    CumulativeEquityCurveBuilder,
    EquityCurveMode,
    PerformanceMetricMode,
    RealizedPnLEngine,
    RiskAdjustedMetricMode,
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
        self.assertIs(report.mode, PerformanceMetricMode.GROSS)

    def test_net_report_requires_matching_upstream_modes(self) -> None:
        """Retain net artifact references while recording explicit report identity."""
        performance, curve, drawdown, risk_metrics = _net_artifacts()

        report = build_backtest_report(
            performance,
            curve,
            drawdown,
            risk_metrics,
            mode=PerformanceMetricMode.NET,
        )

        self.assertIs(report.mode, PerformanceMetricMode.NET)
        self.assertIs(report.performance_metrics, performance)
        self.assertIs(report.equity_curve, curve)
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
        with self.assertRaises(ValueError):
            build_backtest_report(
                performance,
                curve,
                drawdown,
                risk_metrics,
                mode=PerformanceMetricMode.NET,
            )
        with self.assertRaises(ValueError):
            build_backtest_report(
                performance,
                replace(curve, mode=EquityCurveMode.NET),
                drawdown,
                risk_metrics,
            )
        with self.assertRaises(ValueError):
            build_backtest_report(
                performance,
                curve,
                drawdown,
                replace(risk_metrics, mode=RiskAdjustedMetricMode.NET),
            )


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


def _net_artifacts():
    """Build matching net analytics through existing public upstream selectors."""
    trades = (
        _trade(ExecutionSide.LONG, 1, 100.0, 110.0),
        _trade(ExecutionSide.LONG, 1, 100.0, 95.0),
    )
    summary = RealizedPnLEngine(
        FixedRateTransactionCostModel(0.1, 0.0, 0.0, 0.0, 0.0)
    ).calculate(trades)
    performance = BasicPerformanceAnalyzer(PerformanceMetricMode.NET).analyze(
        summary
    )
    curve = CumulativeEquityCurveBuilder(EquityCurveMode.NET).build(summary)
    drawdown = BasicDrawdownAnalyzer().analyze(curve)
    risk_metrics = BasicRiskMetricsAnalyzer().analyze(performance, drawdown)
    return performance, curve, drawdown, risk_metrics
