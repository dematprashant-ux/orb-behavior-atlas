"""Contract tests for dedicated exact-text report file persistence."""

import ast
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from src.engines.performance import ReportWriter, TextReportWriter


class TextReportWriterTests(TestCase):
    """Verify UTF-8 rendered-text writing without report-domain dependencies."""

    def test_writes_exact_content_and_preserves_trailing_newline(self) -> None:
        """Persist supplied rendered text without altering its line endings."""
        with TemporaryDirectory() as directory:
            destination = Path(directory) / "report.md"
            content = "First line\nSecond line\n"

            TextReportWriter().write(content, destination)

            self.assertTrue(destination.is_file())
            self.assertEqual(destination.read_bytes(), content.encode("utf-8"))

    def test_overwrites_existing_content_and_creates_parent_directories(self) -> None:
        """Replace one target through a temporary sibling without stale content."""
        with TemporaryDirectory() as directory:
            destination = Path(directory) / "nested" / "reports" / "report.html"
            destination.parent.mkdir(parents=True)
            destination.write_text("old", encoding="utf-8")

            TextReportWriter().write("new", destination)

            self.assertEqual(destination.read_text(encoding="utf-8"), "new")
            self.assertEqual(
                tuple(path.name for path in destination.parent.iterdir()),
                ("report.html",),
            )

    def test_preserves_utf8_empty_and_large_content(self) -> None:
        """Write valid empty, Unicode, and large rendered text without mutation."""
        with TemporaryDirectory() as directory:
            writer: ReportWriter = TextReportWriter()
            empty_destination = Path(directory) / "empty.txt"
            utf8_destination = Path(directory) / "utf8.txt"
            large_destination = Path(directory) / "large.txt"
            unicode_content = "BANKNIFTY — ₹\n"
            large_content = "0123456789\n" * 100_000

            writer.write("", empty_destination)
            writer.write(unicode_content, utf8_destination)
            writer.write(large_content, large_destination)

            self.assertEqual(empty_destination.read_text(encoding="utf-8"), "")
            self.assertEqual(
                utf8_destination.read_text(encoding="utf-8"),
                unicode_content,
            )
            self.assertEqual(large_destination.read_text(encoding="utf-8"), large_content)

    def test_writer_rejects_intrinsic_misuse(self) -> None:
        """Require text and a file-like explicit Path destination only."""
        writer = TextReportWriter()
        with TemporaryDirectory() as directory:
            with self.assertRaises(TypeError):
                writer.write(b"text", Path(directory) / "report.txt")
            with self.assertRaises(TypeError):
                writer.write("text", "report.txt")
            with self.assertRaises(ValueError):
                writer.write("text", Path())
            with self.assertRaises(ValueError):
                writer.write("text", Path(directory))

    def test_writer_has_no_report_or_rendering_dependencies(self) -> None:
        """Keep file persistence independent from domain and presentation layers."""
        with open(
            "src/engines/performance/writers.py",
            encoding="utf-8",
        ) as source_file:
            tree = ast.parse(source_file.read())
        imported_modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        self.assertEqual(imported_modules, {"pathlib", "tempfile"})
