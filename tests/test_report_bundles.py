"""Contract tests for deterministic in-memory report ZIP bundle creation."""

import ast
from io import BytesIO
from unittest import TestCase
from zipfile import ZipFile

from src.engines.performance import ReportBundleBuilder, StandardReportBundleBuilder


class StandardReportBundleBuilderTests(TestCase):
    """Verify safe, deterministic ZIP packaging of existing report artifacts."""

    def test_empty_mapping_creates_a_complete_empty_archive(self) -> None:
        """Represent no artifacts as a valid deterministic in-memory ZIP file."""
        bundle = StandardReportBundleBuilder().build({})

        self.assertTrue(bundle.startswith(b"PK"))
        with ZipFile(BytesIO(bundle)) as archive:
            self.assertEqual(archive.namelist(), [])

    def test_text_binary_utf8_and_nested_artifacts_are_preserved_exactly(self) -> None:
        """Encode text as UTF-8 and retain binary content and safe nested names."""
        artifacts = {
            "report.pdf": b"%PDF-\x00\xff",
            "nested/report.html": "<h1>ORB — ₹</h1>\n",
            "report.json": '{"net_profit":5.0}',
        }
        bundle = StandardReportBundleBuilder().build(artifacts)

        with ZipFile(BytesIO(bundle)) as archive:
            self.assertEqual(
                archive.namelist(),
                ["nested/report.html", "report.json", "report.pdf"],
            )
            self.assertEqual(archive.read("report.pdf"), artifacts["report.pdf"])
            self.assertEqual(
                archive.read("nested/report.html"),
                artifacts["nested/report.html"].encode("utf-8"),
            )
            self.assertEqual(
                archive.read("report.json"),
                artifacts["report.json"].encode("utf-8"),
            )
            for info in archive.infolist():
                self.assertEqual(info.date_time, (1980, 1, 1, 0, 0, 0))
                self.assertEqual(info.external_attr, 0o100644 << 16)

    def test_bundle_bytes_are_deterministic_and_input_is_not_mutated(self) -> None:
        """Sort entries and preserve supplied mapping values without modification."""
        artifacts = {"b.md": "second\n", "a.json": "first\n"}
        expected = dict(artifacts)
        builder: ReportBundleBuilder = StandardReportBundleBuilder()

        first = builder.build(artifacts)
        second = builder.build(artifacts)

        self.assertEqual(first, second)
        self.assertEqual(artifacts, expected)

    def test_normalized_duplicate_and_unsafe_names_are_rejected(self) -> None:
        """Reject all unsafe paths rather than silently skipping or rewriting them."""
        builder = StandardReportBundleBuilder()
        invalid_names = (
            "",
            "   ",
            "/report.json",
            "C:\\report.json",
            "../report.json",
            "reports/../report.json",
            "reports/",
        )
        for name in invalid_names:
            with self.subTest(name=name), self.assertRaises(ValueError):
                builder.build({name: "content"})
        with self.assertRaises(ValueError):
            builder.build({"report.json": "one", "./report.json": "two"})

    def test_builder_rejects_invalid_mapping_keys_and_values(self) -> None:
        """Require one mapping of string names to text or immutable binary content."""
        builder = StandardReportBundleBuilder()
        with self.assertRaises(TypeError):
            builder.build([])
        with self.assertRaises(TypeError):
            builder.build({1: "content"})
        with self.assertRaises(TypeError):
            builder.build({"report.json": bytearray(b"content")})

    def test_bundle_module_has_no_report_or_filesystem_dependencies(self) -> None:
        """Keep ZIP creation independent from report processing and disk access."""
        with open("src/engines/performance/bundles.py", encoding="utf-8") as source_file:
            tree = ast.parse(source_file.read())
        imported_modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        self.assertEqual(
            imported_modules,
            {"collections.abc", "io", "pathlib", "zipfile"},
        )
