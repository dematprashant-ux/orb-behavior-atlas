"""Contract tests for deterministic plain-data backtest-report serialization."""

from unittest import TestCase

from src.engines.execution import ExecutionSide
from src.engines.performance import (
    BacktestReport,
    BasicDrawdownAnalyzer,
    BasicPerformanceAnalyzer,
    BasicRiskMetricsAnalyzer,
    CumulativeEquityCurveBuilder,
    DictionaryReportSerializer,
    PerformanceMetricMode,
    RealizedPnLEngine,
    ReportSerializer,
    build_backtest_report,
)

from tests.test_realized_pnl import _trade
from tests.test_backtest_report import _net_artifacts


class DictionaryReportSerializerTests(TestCase):
    """Verify pure ordered plain-data serialization of immutable report artifacts."""

    def test_empty_report_preserves_none_and_empty_collections(self) -> None:
        """Represent empty artifacts without fabricating points or ratio values."""
        serialized = DictionaryReportSerializer().serialize(_report(()))

        self.assertEqual(
            tuple(serialized),
            (
                "report_mode",
                "performance_metrics",
                "equity_curve",
                "drawdown_summary",
                "risk_adjusted_metrics",
            ),
        )
        self.assertEqual(serialized["report_mode"], "gross")
        self.assertEqual(
            serialized["equity_curve"],
            {"points": [], "final_equity": 0.0},
        )
        self.assertEqual(
            serialized["drawdown_summary"],
            {"points": [], "maximum_drawdown": 0.0},
        )
        self.assertEqual(
            serialized["risk_adjusted_metrics"],
            {"recovery_factor": None, "return_over_drawdown": None},
        )

    def test_populated_report_serializes_all_fields_in_source_order(self) -> None:
        """Preserve exact field values and ordered source facts without rounding."""
        report = _report((10.0, -5.0))
        serialized = DictionaryReportSerializer().serialize(report)

        self.assertEqual(
            set(serialized["performance_metrics"]),
            {
                "total_trades",
                "winning_trades",
                "losing_trades",
                "flat_trades",
                "gross_profit",
                "gross_loss",
                "net_profit",
                "win_rate",
                "loss_rate",
                "flat_rate",
                "average_trade_pnl",
                "average_winning_trade",
                "average_losing_trade",
                "profit_factor",
                "expectancy",
            },
        )
        self.assertEqual(serialized["equity_curve"]["final_equity"], 5.0)
        self.assertEqual(
            serialized["equity_curve"]["points"],
            [
                {
                    "source_trade_pnl": {"realized_pnl": 10.0},
                    "cumulative_realized_pnl": 10.0,
                },
                {
                    "source_trade_pnl": {"realized_pnl": -5.0},
                    "cumulative_realized_pnl": 5.0,
                },
            ],
        )
        self.assertEqual(
            serialized["drawdown_summary"]["maximum_drawdown"],
            5.0,
        )
        self.assertEqual(
            serialized["drawdown_summary"]["points"][1],
            {
                "source_equity_point": {
                    "source_trade_pnl": {"realized_pnl": -5.0},
                    "cumulative_realized_pnl": 5.0,
                },
                "running_peak": 10.0,
                "drawdown": 5.0,
            },
        )
        self.assertEqual(
            serialized["risk_adjusted_metrics"],
            {"recovery_factor": 1.0, "return_over_drawdown": 1.0},
        )

    def test_serialization_is_deterministic_plain_data_and_non_mutating(
        self,
    ) -> None:
        """Produce equivalent plain data without domain objects or mutation."""
        report = _report((10.0, -5.0))
        serializer: ReportSerializer = DictionaryReportSerializer()

        first = serializer.serialize(report)
        second = serializer.serialize(report)

        self.assertEqual(first, second)
        self.assertEqual(report, _report((10.0, -5.0)))
        _assert_plain_data(self, first)

    def test_net_report_serializes_a_stable_lowercase_mode(self) -> None:
        """Preserve existing upstream net identity without selecting analytics."""
        performance, curve, drawdown, risk_metrics = _net_artifacts()
        report = build_backtest_report(
            performance,
            curve,
            drawdown,
            risk_metrics,
            mode=PerformanceMetricMode.NET,
        )

        serialized = DictionaryReportSerializer().serialize(report)

        self.assertEqual(serialized["report_mode"], "net")

    def test_serializer_rejects_invalid_report_input(self) -> None:
        """Require the canonical immutable report model at the public boundary."""
        with self.assertRaises(TypeError):
            DictionaryReportSerializer().serialize(object())


def _report(realized_pnls: tuple[float, ...]) -> BacktestReport:
    """Build a complete immutable report through existing public analytics APIs."""
    trades = tuple(
        _trade(ExecutionSide.LONG, 1, 100.0, 100.0 + realized_pnl)
        for realized_pnl in realized_pnls
    )
    summary = RealizedPnLEngine().calculate(trades)
    performance = BasicPerformanceAnalyzer().analyze(summary)
    curve = CumulativeEquityCurveBuilder().build(summary)
    drawdown = BasicDrawdownAnalyzer().analyze(curve)
    risk_metrics = BasicRiskMetricsAnalyzer().analyze(performance, drawdown)
    return build_backtest_report(performance, curve, drawdown, risk_metrics)


def _assert_plain_data(test_case: TestCase, value: object) -> None:
    """Assert recursively that serialized values require no domain-model encoder."""
    if isinstance(value, dict):
        for key, item in value.items():
            test_case.assertIsInstance(key, str)
            _assert_plain_data(test_case, item)
        return
    if isinstance(value, list):
        for item in value:
            _assert_plain_data(test_case, item)
        return
    test_case.assertIsInstance(value, (str, bool, int, float, type(None)))
