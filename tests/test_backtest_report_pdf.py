"""Contract tests for deterministic in-memory PDF report rendering."""

import ast
from io import BytesIO
from unittest import TestCase

from pypdf import PdfReader

from src.engines.performance import PdfReportRenderer, StandardPdfReportRenderer

from tests.test_backtest_report_markdown import _empty_report, _populated_report


class StandardPdfReportRendererTests(TestCase):
    """Verify ordered timestamp-free PDF presentation over plain report data."""

    def test_empty_report_produces_complete_pdf_with_na_values(self) -> None:
        """Render all required sections without inventing metrics or point rows."""
        pdf_bytes = StandardPdfReportRenderer().render(_empty_report())
        reader = PdfReader(BytesIO(pdf_bytes))
        text = _extract_text(reader)

        self.assertTrue(pdf_bytes.startswith(b"%PDF-"))
        self.assertGreaterEqual(len(reader.pages), 1)
        self.assertIn("Backtest Report", text)
        self.assertIn("Report Mode: Gross", text)
        self.assertIn("Performance Metrics", text)
        self.assertIn("Risk-Adjusted Metrics", text)
        self.assertIn("Equity Curve", text)
        self.assertIn("Drawdown Summary", text)
        self.assertIn("N/A", text)
        self.assertNotIn("/CreationDate", pdf_bytes.decode("latin1"))
        self.assertNotIn("/ModDate", pdf_bytes.decode("latin1"))

    def test_populated_report_preserves_section_and_collection_order(self) -> None:
        """Render existing metrics and ordered point facts without recalculation."""
        reader = PdfReader(
            BytesIO(StandardPdfReportRenderer().render(_populated_report()))
        )
        text = _extract_text(reader)

        headings = (
            "Backtest Report",
            "Report Mode: Gross",
            "Performance Metrics",
            "Risk-Adjusted Metrics",
            "Equity Curve",
            "Drawdown Summary",
        )
        self.assertEqual(tuple(sorted(headings, key=text.index)), headings)
        self.assertIn("Total Trades", text)
        self.assertIn("Recovery Factor", text)
        self.assertLess(text.index("10.0"), text.index("-5.0"))
        self.assertIn("Maximum Drawdown", text)

    def test_net_mode_is_rendered_once_near_the_report_top(self) -> None:
        """Render a supplied net report identity without analytics recalculation."""
        report = _empty_report()
        report["report_mode"] = "net"
        text = _extract_text(
            PdfReader(BytesIO(StandardPdfReportRenderer().render(report)))
        )

        self.assertEqual(text.count("Report Mode: Net"), 1)

    def test_rendering_is_deterministic_in_content_and_metadata(self) -> None:
        """Verify repeatable extracted content and stable intentional metadata."""
        renderer: PdfReportRenderer = StandardPdfReportRenderer()
        first = PdfReader(BytesIO(renderer.render(_populated_report())))
        second = PdfReader(BytesIO(renderer.render(_populated_report())))

        self.assertEqual(_extract_text(first), _extract_text(second))
        self.assertEqual(first.metadata, second.metadata)
        self.assertEqual(first.metadata.title, "Backtest Report")
        self.assertNotIn("/CreationDate", first.metadata)
        self.assertNotIn("/ModDate", first.metadata)

    def test_renderer_rejects_invalid_plain_data_and_has_no_report_dependencies(
        self,
    ) -> None:
        """Require serializer-shaped structures while keeping no domain imports."""
        with self.assertRaises(TypeError):
            StandardPdfReportRenderer().render([])
        malformed = _empty_report()
        del malformed["equity_curve"]
        with self.assertRaises(ValueError):
            StandardPdfReportRenderer().render(malformed)
        malformed = _empty_report()
        malformed["drawdown_summary"]["points"] = ()
        with self.assertRaises(TypeError):
            StandardPdfReportRenderer().render(malformed)

        with open("src/engines/performance/pdf.py", encoding="utf-8") as source_file:
            tree = ast.parse(source_file.read())
        imported_modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        self.assertEqual(
            imported_modules,
            {
                "collections.abc",
                "dataclasses",
                "html",
                "io",
                "pathlib",
                "pypdf",
                "reportlab.lib",
                "reportlab.lib.pagesizes",
                "reportlab.lib.styles",
                "reportlab.lib.units",
                "reportlab.pdfbase",
                "reportlab.pdfbase.ttfonts",
                "reportlab.platypus",
            },
        )


def _extract_text(reader: PdfReader) -> str:
    """Extract ordered visible text solely for PDF content assertions."""
    return "\n".join(page.extract_text() or "" for page in reader.pages)
