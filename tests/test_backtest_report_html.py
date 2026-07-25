"""Contract tests for deterministic standalone HTML report rendering."""

import ast
from copy import deepcopy
from dataclasses import FrozenInstanceError, is_dataclass
from unittest import TestCase

from src.engines.performance import HtmlReportRenderer, StandardHtmlReportRenderer

from tests.test_backtest_report_markdown import _empty_report, _populated_report


class StandardHtmlReportRendererTests(TestCase):
    """Verify safe standalone HTML presentation over existing plain report data."""

    def test_empty_report_is_a_complete_standalone_document(self) -> None:
        """Render all required metadata, sections, tables, and unavailable values."""
        rendered = StandardHtmlReportRenderer().render(_empty_report())

        self.assertTrue(rendered.startswith("<!DOCTYPE html>\n<html lang=\"en\">"))
        self.assertIn('<meta charset="utf-8">', rendered)
        self.assertIn(
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            rendered,
        )
        self.assertIn("<title>Backtest Report</title>", rendered)
        self.assertIn("<style>", rendered)
        self.assertIn("@media print", rendered)
        self.assertIn("<body>", rendered)
        self.assertEqual(rendered.count(">Report Mode<"), 1)
        self.assertEqual(rendered.count(">Gross<"), 1)
        self.assertEqual(rendered.count(">N/A<"), 3)
        self.assertNotIn("<script", rendered)
        self.assertNotIn("src=", rendered)
        self.assertNotIn("href=", rendered)
        self.assertNotIn("http", rendered)
        self.assertNotIn("<!--", rendered)

    def test_populated_report_preserves_stable_sections_fields_and_point_order(
        self,
    ) -> None:
        """Render every supplied fact once without calculations or reordered rows."""
        rendered = StandardHtmlReportRenderer().render(_populated_report())

        headings = (
            "<h1>Backtest Report</h1>",
            "<h2 id=\"report-mode\">Report Mode</h2>",
            "<h2 id=\"performance-metrics\">Performance Metrics</h2>",
            "<h2 id=\"risk-adjusted-metrics\">Risk-Adjusted Metrics</h2>",
            "<h2 id=\"equity-curve\">Equity Curve</h2>",
            "<h2 id=\"drawdown-summary\">Drawdown Summary</h2>",
        )
        self.assertEqual(tuple(sorted(headings, key=rendered.index)), headings)
        for label in _performance_labels():
            self.assertEqual(rendered.count(f">{label}<"), 1)
        self.assertEqual(rendered.count(">Recovery Factor<"), 1)
        self.assertEqual(rendered.count(">Return Over Drawdown<"), 1)
        self.assertLess(
            rendered.index(">10.0</td><td>10.0<"),
            rendered.index(">-5.0</td><td>5.0<"),
        )
        self.assertIn(
            ">-5.0</td><td>5.0</td><td>10.0</td><td>5.0</td>",
            rendered,
        )

    def test_net_mode_is_rendered_once_near_the_report_top(self) -> None:
        """Render only the supplied serialized net identity in semantic markup."""
        report = _empty_report()
        report["report_mode"] = "net"

        rendered = StandardHtmlReportRenderer().render(report)

        self.assertEqual(rendered.count(">Report Mode<"), 1)
        self.assertEqual(rendered.count(">Net<"), 1)

    def test_dynamic_text_is_escaped_and_output_is_deterministic(self) -> None:
        """Escape serialized string content and retain stable standalone output."""
        report = _populated_report()
        performance = report["performance_metrics"]
        assert isinstance(performance, dict)
        performance["expectancy"] = '<unsafe & "quoted">'
        renderer: HtmlReportRenderer = StandardHtmlReportRenderer()

        first = renderer.render(report)
        second = renderer.render(report)

        self.assertEqual(first, second)
        self.assertIn("&lt;unsafe &amp; &quot;quoted&quot;&gt;", first)
        self.assertNotIn('<unsafe & "quoted">', first)

    def test_renderer_is_immutable_newline_terminated_and_non_mutating(self) -> None:
        """Leave nested input data unchanged and return exactly one final newline."""
        report = _populated_report()
        expected = deepcopy(report)
        renderer = StandardHtmlReportRenderer()

        rendered = renderer.render(report)

        self.assertTrue(rendered.endswith("\n"))
        self.assertFalse(rendered.endswith("\n\n"))
        self.assertEqual(report, expected)
        self.assertTrue(is_dataclass(renderer))
        self.assertFalse(hasattr(renderer, "__dict__"))
        with self.assertRaises((FrozenInstanceError, TypeError)):
            renderer.unused = None

    def test_renderer_rejects_invalid_plain_data_and_has_no_domain_dependencies(
        self,
    ) -> None:
        """Require serializer-shaped data while retaining no analytics dependencies."""
        with self.assertRaises(TypeError):
            StandardHtmlReportRenderer().render([])
        malformed = _empty_report()
        del malformed["drawdown_summary"]
        with self.assertRaises(ValueError):
            StandardHtmlReportRenderer().render(malformed)
        malformed = _empty_report()
        malformed["drawdown_summary"]["points"] = ()
        with self.assertRaises(TypeError):
            StandardHtmlReportRenderer().render(malformed)

        with open(
            "src/engines/performance/html.py",
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
            {"collections.abc", "dataclasses", "html"},
        )


def _performance_labels() -> tuple[str, ...]:
    """Return the stable human-readable PerformanceMetrics label sequence."""
    return (
        "Total Trades",
        "Winning Trades",
        "Losing Trades",
        "Flat Trades",
        "Gross Profit",
        "Gross Loss",
        "Net Profit",
        "Win Rate",
        "Loss Rate",
        "Flat Rate",
        "Average Trade PnL",
        "Average Winning Trade",
        "Average Losing Trade",
        "Profit Factor",
        "Expectancy",
    )
