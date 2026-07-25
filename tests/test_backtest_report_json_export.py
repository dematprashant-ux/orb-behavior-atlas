"""Contract tests for deterministic compact JSON backtest-report export."""

import ast
import json
from dataclasses import FrozenInstanceError, is_dataclass
from unittest import TestCase

from src.engines.execution import ExecutionSide
from src.engines.performance import (
    BasicDrawdownAnalyzer,
    BasicPerformanceAnalyzer,
    BasicRiskMetricsAnalyzer,
    CumulativeEquityCurveBuilder,
    DictionaryReportSerializer,
    JsonReportExporter,
    RealizedPnLEngine,
    StandardJsonReportExporter,
    build_backtest_report,
)

from tests.test_realized_pnl import _trade


class StandardJsonReportExporterTests(TestCase):
    """Verify pure stable JSON encoding of serializer-produced plain data."""

    def test_empty_report_export_is_compact_and_preserves_nulls(self) -> None:
        """Encode empty ordered collections and unavailable ratios without strings."""
        exported = _export(())
        decoded = json.loads(exported)

        self.assertNotIn("\n", exported)
        self.assertNotIn(" ", exported)
        self.assertEqual(decoded["equity_curve"], {"final_equity": 0.0, "points": []})
        self.assertEqual(
            decoded["risk_adjusted_metrics"],
            {"recovery_factor": None, "return_over_drawdown": None},
        )

    def test_populated_export_preserves_numbers_and_collection_order(self) -> None:
        """Encode exact source values without rounding or reordering lists."""
        exported = _export((10.0, -5.0))
        decoded = json.loads(exported)

        self.assertEqual(decoded["performance_metrics"]["net_profit"], 5.0)
        self.assertEqual(decoded["equity_curve"]["final_equity"], 5.0)
        self.assertEqual(
            [
                point["source_trade_pnl"]["realized_pnl"]
                for point in decoded["equity_curve"]["points"]
            ],
            [10.0, -5.0],
        )
        self.assertEqual(decoded["drawdown_summary"]["maximum_drawdown"], 5.0)
        self.assertEqual(decoded["risk_adjusted_metrics"]["recovery_factor"], 1.0)

    def test_export_is_deterministic_and_has_stable_key_order(self) -> None:
        """Produce equal compact JSON and lexicographically ordered object keys."""
        serialized = DictionaryReportSerializer().serialize(_report((10.0, -5.0)))
        exporter: JsonReportExporter = StandardJsonReportExporter()

        first = exporter.export(serialized)
        second = exporter.export(serialized)

        self.assertEqual(first, second)
        self.assertEqual(
            tuple(json.loads(first)),
            (
                "drawdown_summary",
                "equity_curve",
                "performance_metrics",
                "risk_adjusted_metrics",
            ),
        )

    def test_exporter_is_immutable_and_does_not_mutate_plain_input(self) -> None:
        """Keep the exporter stateless and leave supplied nested data unchanged."""
        serialized = DictionaryReportSerializer().serialize(_report((10.0, -5.0)))
        expected = json.loads(json.dumps(serialized))
        exporter = StandardJsonReportExporter()

        exporter.export(serialized)

        self.assertTrue(is_dataclass(exporter))
        self.assertFalse(hasattr(exporter, "__dict__"))
        self.assertEqual(serialized, expected)
        with self.assertRaises((FrozenInstanceError, TypeError)):
            exporter.unused = None

    def test_exporter_rejects_invalid_input_and_has_no_domain_dependencies(self) -> None:
        """Require plain mapping input and retain no analytics-domain imports."""
        with self.assertRaises(TypeError):
            StandardJsonReportExporter().export([])

        with open(
            "src/engines/performance/json_export.py",
            encoding="utf-8",
        ) as source_file:
            tree = ast.parse(source_file.read())
        imported_modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        self.assertEqual(imported_modules, {"collections.abc", "dataclasses"})


def _export(realized_pnls: tuple[float, ...]) -> str:
    """Serialize a complete report and export it through public boundaries."""
    serialized = DictionaryReportSerializer().serialize(_report(realized_pnls))
    return StandardJsonReportExporter().export(serialized)


def _report(realized_pnls: tuple[float, ...]):
    """Build an immutable report with existing public analytics contracts."""
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
