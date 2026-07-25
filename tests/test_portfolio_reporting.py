"""Contract tests for immutable portfolio reporting and existing renderers."""

from dataclasses import FrozenInstanceError, is_dataclass
from datetime import datetime, timedelta, timezone
from unittest import TestCase

from pypdf import PdfReader

from src.engines.performance import (
    StandardHtmlReportRenderer,
    StandardJsonReportExporter,
    StandardMarkdownReportRenderer,
    StandardPdfReportRenderer,
)
from src.engines.portfolio import (
    DictionaryPortfolioReportSerializer,
    PortfolioReport,
    StandardPortfolioDrawdownAnalyzer,
    StandardPortfolioPerformanceAnalyzer,
    build_portfolio_equity_curve,
    build_portfolio_equity_point,
    build_portfolio_report,
)


class PortfolioReportingTests(TestCase):
    """Verify portfolio presentation composes upstream facts without analytics."""

    def test_report_retains_upstream_references_and_is_immutable(self) -> None:
        """Compose completed analytics without copying values or recalculation."""
        curve = _curve()
        metrics = StandardPortfolioPerformanceAnalyzer().analyze(curve)
        drawdown = StandardPortfolioDrawdownAnalyzer().analyze(curve)
        report = build_portfolio_report(metrics, curve, drawdown)

        self.assertIs(report.performance_metrics, metrics)
        self.assertIs(report.equity_curve, curve)
        self.assertIs(report.drawdown_summary, drawdown)
        self.assertTrue(is_dataclass(report))
        self.assertFalse(hasattr(report, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            report.equity_curve = _curve()

    def test_serializer_returns_stable_plain_data_with_ordered_points(self) -> None:
        """Serialize only supplied facts into JSON-safe strings, lists, and scalars."""
        serialized = DictionaryPortfolioReportSerializer().serialize(_report())

        self.assertEqual(serialized["report_type"], "portfolio")
        self.assertEqual(
            list(serialized["performance_metrics"]),
            [
                "initial_equity",
                "final_equity",
                "absolute_return",
                "total_return",
                "maximum_equity",
                "minimum_equity",
                "equity_point_count",
            ],
        )
        points = serialized["equity_curve"]["points"]
        self.assertEqual([point["total_equity"] for point in points], [100.0, 125.0])
        self.assertIsInstance(points[0]["timestamp"], str)
        exporter = StandardJsonReportExporter()
        self.assertEqual(exporter.export(serialized), exporter.export(serialized))

    def test_existing_text_and_pdf_renderers_render_portfolio_plain_data(self) -> None:
        """Reuse generic presentation boundaries without a second renderer engine."""
        serialized = DictionaryPortfolioReportSerializer().serialize(_report())
        markdown = StandardMarkdownReportRenderer().render(serialized)
        html = StandardHtmlReportRenderer().render(serialized)
        pdf = StandardPdfReportRenderer().render(serialized)

        self.assertIn("# Portfolio Report", markdown)
        self.assertEqual(markdown.count("Initial Equity"), 1)
        self.assertIn("Maximum Drawdown", markdown)
        self.assertTrue(markdown.endswith("\n"))
        self.assertIn("<h1>Portfolio Report</h1>", html)
        self.assertIn("Maximum Drawdown", html)
        self.assertIn("<td>125.0</td>", html)
        reader = PdfReader(__import__("io").BytesIO(pdf))
        text = "".join(page.extract_text() or "" for page in reader.pages)
        self.assertIn("Portfolio Report", text)
        self.assertIn("Initial Equity", text)
        self.assertIn("Maximum Drawdown", text)

    def test_reporting_rejects_intrinsic_misuse_without_consistency_analysis(
        self,
    ) -> None:
        """Require only report model types and serializer input type at this layer."""
        with self.assertRaises(TypeError):
            build_portfolio_report(object(), _curve(), _drawdown())
        with self.assertRaises(TypeError):
            DictionaryPortfolioReportSerializer().serialize(object())


def _report() -> PortfolioReport:
    """Build one completed deterministic portfolio report fixture."""
    return build_portfolio_report(_metrics(), _curve(), _drawdown())


def _metrics():
    """Return metrics derived once from the fixture curve."""
    return StandardPortfolioPerformanceAnalyzer().analyze(_curve())


def _drawdown():
    """Return drawdown derived once from the fixture curve."""
    return StandardPortfolioDrawdownAnalyzer().analyze(_curve())


def _curve():
    """Return an ordered two-point curve with one explicit return observation."""
    return build_portfolio_equity_curve(
        (
            build_portfolio_equity_point(_timestamp(0), 100.0, 0.0),
            build_portfolio_equity_point(_timestamp(1), 100.0, 25.0),
        )
    )


def _timestamp(minutes: int) -> datetime:
    """Return explicit aware timestamps without introducing report metadata."""
    return datetime(2026, 1, 1, 9, 15, tzinfo=timezone.utc) + timedelta(
        minutes=minutes
    )
