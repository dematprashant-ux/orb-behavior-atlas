"""Contract tests for deterministic in-memory Markdown report rendering."""

import ast
from copy import deepcopy
from dataclasses import FrozenInstanceError, is_dataclass
from unittest import TestCase

from src.engines.performance import (
    MarkdownReportRenderer,
    StandardMarkdownReportRenderer,
)


class StandardMarkdownReportRendererTests(TestCase):
    """Verify stable Markdown presentation over existing plain report data."""

    def test_empty_report_renders_required_sections_and_na_values(self) -> None:
        """Render empty lists and unavailable ratios without inventing values."""
        rendered = StandardMarkdownReportRenderer().render(_empty_report())

        self.assertEqual(
            rendered,
            "# Backtest Report\n\n"
            "| Report Mode |\n"
            "| --- |\n"
            "| Gross |\n\n"
            "## Performance Metrics\n\n"
            "| Metric | Value |\n"
            "| --- | --- |\n"
            "| Total Trades | 0 |\n"
            "| Winning Trades | 0 |\n"
            "| Losing Trades | 0 |\n"
            "| Flat Trades | 0 |\n"
            "| Gross Profit | 0.0 |\n"
            "| Gross Loss | 0.0 |\n"
            "| Net Profit | 0.0 |\n"
            "| Win Rate | 0.0 |\n"
            "| Loss Rate | 0.0 |\n"
            "| Flat Rate | 0.0 |\n"
            "| Average Trade PnL | 0.0 |\n"
            "| Average Winning Trade | 0.0 |\n"
            "| Average Losing Trade | 0.0 |\n"
            "| Profit Factor | N/A |\n"
            "| Expectancy | 0.0 |\n\n"
            "## Risk-Adjusted Metrics\n\n"
            "| Metric | Value |\n"
            "| --- | --- |\n"
            "| Recovery Factor | N/A |\n"
            "| Return Over Drawdown | N/A |\n\n"
            "## Equity Curve\n\n"
            "| Final Equity |\n"
            "| --- |\n"
            "| 0.0 |\n\n"
            "| Source Trade PnL | Cumulative Realized PnL |\n"
            "| --- | --- |\n\n"
            "## Drawdown Summary\n\n"
            "| Maximum Drawdown |\n"
            "| --- |\n"
            "| 0.0 |\n\n"
            "| Source Trade PnL | Cumulative Realized PnL | Running Peak | Drawdown |\n"
            "| --- | --- | --- | --- |\n",
        )

    def test_populated_report_preserves_metrics_and_point_order(self) -> None:
        """Render every existing value once in stable table columns and order."""
        rendered = StandardMarkdownReportRenderer().render(_populated_report())

        self.assertLess(
            rendered.index("# Backtest Report"),
            rendered.index("| Report Mode |"),
        )
        self.assertLess(
            rendered.index("| Report Mode |"),
            rendered.index("## Performance Metrics"),
        )
        self.assertEqual(rendered.count("Report Mode"), 1)
        self.assertEqual(rendered.count("| Gross |"), 1)
        self.assertLess(
            rendered.index("## Performance Metrics"),
            rendered.index("## Risk-Adjusted Metrics"),
        )
        self.assertLess(
            rendered.index("## Risk-Adjusted Metrics"),
            rendered.index("## Equity Curve"),
        )
        self.assertLess(
            rendered.index("## Equity Curve"),
            rendered.index("## Drawdown Summary"),
        )
        for label in _performance_labels():
            self.assertEqual(rendered.count(f"| {label} |"), 1)
        self.assertEqual(rendered.count("| Recovery Factor |"), 1)
        self.assertEqual(rendered.count("| Return Over Drawdown |"), 1)
        self.assertIn("| 10.0 | 10.0 |", rendered)
        self.assertIn("| -5.0 | 5.0 |", rendered)
        self.assertLess(
            rendered.index("| 10.0 | 10.0 |"),
            rendered.index("| -5.0 | 5.0 |"),
        )
        self.assertIn("| -5.0 | 5.0 | 10.0 | 5.0 |", rendered)

    def test_rendering_is_deterministic_newline_terminated_and_non_mutating(
        self,
    ) -> None:
        """Return stable output without changing the supplied nested plain data."""
        report = _populated_report()
        expected = deepcopy(report)
        renderer: MarkdownReportRenderer = StandardMarkdownReportRenderer()

        first = renderer.render(report)
        second = renderer.render(report)

        self.assertEqual(first, second)
        self.assertTrue(first.endswith("\n"))
        self.assertFalse(first.endswith("\n\n"))
        self.assertEqual(report, expected)
        self.assertTrue(is_dataclass(renderer))
        self.assertFalse(hasattr(renderer, "__dict__"))
        with self.assertRaises((FrozenInstanceError, TypeError)):
            renderer.unused = None

    def test_renderer_rejects_invalid_required_sections_and_point_collections(
        self,
    ) -> None:
        """Require serializer-shaped mappings and ordered point lists only."""
        with self.assertRaises(TypeError):
            StandardMarkdownReportRenderer().render([])
        malformed = _empty_report()
        del malformed["equity_curve"]
        with self.assertRaises(ValueError):
            StandardMarkdownReportRenderer().render(malformed)
        malformed = _empty_report()
        malformed["equity_curve"]["points"] = ()
        with self.assertRaises(TypeError):
            StandardMarkdownReportRenderer().render(malformed)
        malformed = _empty_report()
        malformed["report_mode"] = "invalid"
        with self.assertRaises(ValueError):
            StandardMarkdownReportRenderer().render(malformed)

    def test_net_mode_is_displayed_once_near_the_report_top(self) -> None:
        """Render an existing serialized net identity without interpretation."""
        report = _empty_report()
        report["report_mode"] = "net"

        rendered = StandardMarkdownReportRenderer().render(report)

        self.assertEqual(rendered.count("Report Mode"), 1)
        self.assertEqual(rendered.count("| Net |"), 1)

    def test_renderer_has_only_plain_data_dependencies(self) -> None:
        """Keep Markdown presentation independent from analytics and I/O layers."""
        with open(
            "src/engines/performance/markdown.py",
            encoding="utf-8",
        ) as source_file:
            tree = ast.parse(source_file.read())
        imported_modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        self.assertEqual(imported_modules, {"collections.abc", "dataclasses"})


def _empty_report() -> dict[str, object]:
    """Return one minimal plain serializer-shaped report with no point rows."""
    return {
        "report_mode": "gross",
        "performance_metrics": {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "flat_trades": 0,
            "gross_profit": 0.0,
            "gross_loss": 0.0,
            "net_profit": 0.0,
            "win_rate": 0.0,
            "loss_rate": 0.0,
            "flat_rate": 0.0,
            "average_trade_pnl": 0.0,
            "average_winning_trade": 0.0,
            "average_losing_trade": 0.0,
            "profit_factor": None,
            "expectancy": 0.0,
        },
        "risk_adjusted_metrics": {
            "recovery_factor": None,
            "return_over_drawdown": None,
        },
        "equity_curve": {"points": [], "final_equity": 0.0},
        "drawdown_summary": {"points": [], "maximum_drawdown": 0.0},
    }


def _populated_report() -> dict[str, object]:
    """Return serializer-shaped plain data with ordered source-point facts."""
    report = _empty_report()
    performance = report["performance_metrics"]
    assert isinstance(performance, dict)
    performance.update(
        {
            "total_trades": 2,
            "winning_trades": 1,
            "losing_trades": 1,
            "gross_profit": 10.0,
            "gross_loss": 5.0,
            "net_profit": 5.0,
            "win_rate": 0.5,
            "loss_rate": 0.5,
            "average_trade_pnl": 2.5,
            "average_winning_trade": 10.0,
            "average_losing_trade": -5.0,
            "profit_factor": 2.0,
            "expectancy": 2.5,
        }
    )
    report["risk_adjusted_metrics"] = {
        "recovery_factor": 1.0,
        "return_over_drawdown": 1.0,
    }
    report["equity_curve"] = {
        "points": [
            {
                "source_trade_pnl": {"realized_pnl": 10.0},
                "cumulative_realized_pnl": 10.0,
            },
            {
                "source_trade_pnl": {"realized_pnl": -5.0},
                "cumulative_realized_pnl": 5.0,
            },
        ],
        "final_equity": 5.0,
    }
    report["drawdown_summary"] = {
        "points": [
            {
                "source_equity_point": {
                    "source_trade_pnl": {"realized_pnl": 10.0},
                    "cumulative_realized_pnl": 10.0,
                },
                "running_peak": 10.0,
                "drawdown": 0.0,
            },
            {
                "source_equity_point": {
                    "source_trade_pnl": {"realized_pnl": -5.0},
                    "cumulative_realized_pnl": 5.0,
                },
                "running_peak": 10.0,
                "drawdown": 5.0,
            },
        ],
        "maximum_drawdown": 5.0,
    }
    return report


def _performance_labels() -> tuple[str, ...]:
    """Return the required human-readable labels in renderer column order."""
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
