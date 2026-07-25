"""Contract tests for binary PDF and multi-format bundle export orchestration."""

import ast
from dataclasses import FrozenInstanceError, is_dataclass
from pathlib import Path
from unittest import TestCase

from src.engines.performance import (
    BinaryReportExportService,
    StandardBinaryReportExportService,
)


class StandardBinaryReportExportServiceTests(TestCase):
    """Verify exact injected collaborator sequencing for binary report exports."""

    def test_pdf_export_serializes_once_and_writes_unmodified_pdf_bytes(self) -> None:
        """Route the exact PDF renderer output directly to the binary writer."""
        events: list[tuple[object, ...]] = []
        service = _service(events)
        report = object()
        destination = Path("report.pdf")

        service.export_pdf(report, destination)

        self.assertEqual(
            events,
            [
                ("serialize", report),
                ("pdf_render", _SERIALIZED),
                ("binary_write", _PDF_BYTES, destination),
            ],
        )

    def test_bundle_export_uses_fixed_artifacts_and_stable_invocation_order(self) -> None:
        """Produce every format from one shared serialized object before writing ZIP."""
        events: list[tuple[object, ...]] = []
        service = _service(events)
        report = object()
        destination = Path("report.zip")

        service.export_bundle(report, destination)

        expected_artifacts = {
            "report.json": _JSON_TEXT,
            "report.md": _MARKDOWN_TEXT,
            "report.html": _HTML_TEXT,
            "report.pdf": _PDF_BYTES,
        }
        self.assertEqual(
            events,
            [
                ("serialize", report),
                ("json_export", _SERIALIZED),
                ("markdown_render", _SERIALIZED),
                ("html_render", _SERIALIZED),
                ("pdf_render", _SERIALIZED),
                ("bundle_build", expected_artifacts),
                ("binary_write", _BUNDLE_BYTES, destination),
            ],
        )
        for event in events[1:5]:
            self.assertIs(event[1], _SERIALIZED)
        bundle_artifacts = events[5][1]
        self.assertIs(bundle_artifacts["report.json"], _JSON_TEXT)
        self.assertIs(bundle_artifacts["report.md"], _MARKDOWN_TEXT)
        self.assertIs(bundle_artifacts["report.html"], _HTML_TEXT)
        self.assertIs(bundle_artifacts["report.pdf"], _PDF_BYTES)

    def test_service_retains_injected_dependencies_and_is_immutable(self) -> None:
        """Store exact collaborator objects without constructing replacements."""
        events: list[tuple[object, ...]] = []
        dependencies = _dependencies(events)
        service: BinaryReportExportService = StandardBinaryReportExportService(
            *dependencies
        )

        self.assertIs(service.serializer, dependencies[0])
        self.assertIs(service.json_exporter, dependencies[1])
        self.assertIs(service.markdown_renderer, dependencies[2])
        self.assertIs(service.html_renderer, dependencies[3])
        self.assertIs(service.pdf_renderer, dependencies[4])
        self.assertIs(service.bundle_builder, dependencies[5])
        self.assertIs(service.binary_writer, dependencies[6])
        self.assertTrue(is_dataclass(service))
        self.assertFalse(hasattr(service, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            service.binary_writer = dependencies[6]

    def test_producer_failure_propagates_without_bundle_or_writer_invocation(self) -> None:
        """Stop bundle export immediately when a producer cannot create content."""
        events: list[tuple[object, ...]] = []
        dependencies = list(_dependencies(events))
        dependencies[1] = _FailingJsonExporter(events)
        service = StandardBinaryReportExportService(*dependencies)
        report = object()

        with self.assertRaisesRegex(RuntimeError, "json export failed"):
            service.export_bundle(report, Path("report.zip"))

        self.assertEqual(events, [("serialize", report), ("json_export", _SERIALIZED)])

    def test_service_rejects_missing_dependencies_and_has_no_producer_implementations(self) -> None:
        """Reject absent collaborators without reflection or collaborator calls."""
        events: list[tuple[object, ...]] = []
        dependencies = list(_dependencies(events))
        dependencies[5] = None
        with self.assertRaises(TypeError):
            StandardBinaryReportExportService(*dependencies)

        with open(
            "src/engines/performance/binary_export_service.py",
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
            {
                "dataclasses",
                "pathlib",
                "src.engines.performance.interfaces",
                "src.engines.performance.models",
            },
        )


_SERIALIZED = {"report": "plain"}
_JSON_TEXT = '{"report":"plain"}'
_MARKDOWN_TEXT = "# Report\n"
_HTML_TEXT = "<h1>Report</h1>"
_PDF_BYTES = b"%PDF-1.7"
_BUNDLE_BYTES = b"PK\x03\x04"


def _service(events: list[tuple[object, ...]]) -> StandardBinaryReportExportService:
    """Build a service from all required recording collaborators."""
    return StandardBinaryReportExportService(*_dependencies(events))


def _dependencies(events: list[tuple[object, ...]]) -> tuple[object, ...]:
    """Return one complete ordered collaborator tuple for injection tests."""
    return (
        _Serializer(events),
        _JsonExporter(events),
        _MarkdownRenderer(events),
        _HtmlRenderer(events),
        _PdfRenderer(events),
        _BundleBuilder(events),
        _BinaryWriter(events),
    )


class _Serializer:
    """Record serializer calls and return one shared plain serialized object."""

    def __init__(self, events: list[tuple[object, ...]]) -> None:
        self._events = events

    def serialize(self, report: object) -> dict[str, str]:
        """Record the exact report object without inspecting it."""
        self._events.append(("serialize", report))
        return _SERIALIZED


class _JsonExporter:
    """Record JSON export calls and return fixed existing text."""

    def __init__(self, events: list[tuple[object, ...]]) -> None:
        self._events = events

    def export(self, serialized_report: object) -> str:
        """Record the exact shared serialized object received."""
        self._events.append(("json_export", serialized_report))
        return _JSON_TEXT


class _FailingJsonExporter(_JsonExporter):
    """Raise a controlled producer failure after recording its invocation."""

    def export(self, serialized_report: object) -> str:
        """Record and propagate a production failure without fallback output."""
        self._events.append(("json_export", serialized_report))
        raise RuntimeError("json export failed")


class _MarkdownRenderer:
    """Record Markdown render calls and return fixed existing text."""

    def __init__(self, events: list[tuple[object, ...]]) -> None:
        self._events = events

    def render(self, serialized_report: object) -> str:
        """Record the exact shared serialized object received."""
        self._events.append(("markdown_render", serialized_report))
        return _MARKDOWN_TEXT


class _HtmlRenderer:
    """Record HTML render calls and return fixed existing text."""

    def __init__(self, events: list[tuple[object, ...]]) -> None:
        self._events = events

    def render(self, serialized_report: object) -> str:
        """Record the exact shared serialized object received."""
        self._events.append(("html_render", serialized_report))
        return _HTML_TEXT


class _PdfRenderer:
    """Record PDF render calls and return fixed existing binary bytes."""

    def __init__(self, events: list[tuple[object, ...]]) -> None:
        self._events = events

    def render(self, serialized_report: object) -> bytes:
        """Record the exact shared serialized object received."""
        self._events.append(("pdf_render", serialized_report))
        return _PDF_BYTES


class _BundleBuilder:
    """Record exact artifact mappings and return fixed existing ZIP bytes."""

    def __init__(self, events: list[tuple[object, ...]]) -> None:
        self._events = events

    def build(self, artifacts: object) -> bytes:
        """Record the artifact mapping without modifying its child values."""
        self._events.append(("bundle_build", artifacts))
        return _BUNDLE_BYTES


class _BinaryWriter:
    """Record final bytes and destination without performing file I/O."""

    def __init__(self, events: list[tuple[object, ...]]) -> None:
        self._events = events

    def write(self, content: bytes, destination: Path) -> None:
        """Record the exact bytes and path received from orchestration."""
        self._events.append(("binary_write", content, destination))
