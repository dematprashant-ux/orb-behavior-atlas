"""Contract tests for dependency-injected report export orchestration."""

import ast
from dataclasses import FrozenInstanceError, is_dataclass
from pathlib import Path
from unittest import TestCase

from src.engines.performance import (
    ReportExportService,
    StandardReportExportService,
)


class StandardReportExportServiceTests(TestCase):
    """Verify strict serializer-to-producer-to-writer orchestration order."""

    def test_json_export_orchestrates_collaborators_in_order(self) -> None:
        """Pass the serializer output directly through JSON export and writing."""
        events: list[tuple[object, ...]] = []
        service = _service(events)
        report = object()
        destination = Path("report.json")

        service.export_json(report, destination)

        self.assertEqual(
            events,
            [
                ("serialize", report),
                ("json_export", {"report": "plain"}),
                ("write", "json text", destination),
            ],
        )

    def test_markdown_export_orchestrates_collaborators_in_order(self) -> None:
        """Pass the serializer output directly through Markdown and writing."""
        events: list[tuple[object, ...]] = []
        service = _service(events)
        report = object()
        destination = Path("report.md")

        service.export_markdown(report, destination)

        self.assertEqual(
            events,
            [
                ("serialize", report),
                ("markdown_render", {"report": "plain"}),
                ("write", "markdown text", destination),
            ],
        )

    def test_html_export_orchestrates_collaborators_in_order(self) -> None:
        """Pass the serializer output directly through HTML and writing."""
        events: list[tuple[object, ...]] = []
        service = _service(events)
        report = object()
        destination = Path("report.html")

        service.export_html(report, destination)

        self.assertEqual(
            events,
            [
                ("serialize", report),
                ("html_render", {"report": "plain"}),
                ("write", "html text", destination),
            ],
        )

    def test_service_retains_injected_dependencies_and_is_immutable(self) -> None:
        """Store exact collaborator objects without constructing replacements."""
        events: list[tuple[object, ...]] = []
        serializer = _Serializer(events)
        json_exporter = _JsonExporter(events)
        markdown_renderer = _MarkdownRenderer(events)
        html_renderer = _HtmlRenderer(events)
        writer = _Writer(events)
        service: ReportExportService = StandardReportExportService(
            serializer,
            json_exporter,
            markdown_renderer,
            html_renderer,
            writer,
        )

        self.assertIs(service.serializer, serializer)
        self.assertIs(service.json_exporter, json_exporter)
        self.assertIs(service.markdown_renderer, markdown_renderer)
        self.assertIs(service.html_renderer, html_renderer)
        self.assertIs(service.writer, writer)
        self.assertTrue(is_dataclass(service))
        self.assertFalse(hasattr(service, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            service.writer = writer

    def test_service_rejects_missing_dependencies_and_has_no_implementations(self) -> None:
        """Reject absent collaborators without performing protocol reflection."""
        events: list[tuple[object, ...]] = []
        serializer = _Serializer(events)
        json_exporter = _JsonExporter(events)
        markdown_renderer = _MarkdownRenderer(events)
        html_renderer = _HtmlRenderer(events)
        writer = _Writer(events)

        with self.assertRaises(TypeError):
            StandardReportExportService(
                None,
                json_exporter,
                markdown_renderer,
                html_renderer,
                writer,
            )

        with open(
            "src/engines/performance/export_service.py",
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


def _service(events: list[tuple[object, ...]]) -> StandardReportExportService:
    """Build one service from lightweight injected test doubles."""
    return StandardReportExportService(
        _Serializer(events),
        _JsonExporter(events),
        _MarkdownRenderer(events),
        _HtmlRenderer(events),
        _Writer(events),
    )


class _Serializer:
    """Record serializer invocation while returning fixed plain data."""

    def __init__(self, events: list[tuple[object, ...]]) -> None:
        self._events = events

    def serialize(self, report: object) -> dict[str, str]:
        """Record the exact report reference received by orchestration."""
        self._events.append(("serialize", report))
        return {"report": "plain"}


class _JsonExporter:
    """Record JSON export invocation while returning existing text."""

    def __init__(self, events: list[tuple[object, ...]]) -> None:
        self._events = events

    def export(self, serialized_report: object) -> str:
        """Record the exact plain serialized object received."""
        self._events.append(("json_export", serialized_report))
        return "json text"


class _MarkdownRenderer:
    """Record Markdown rendering invocation while returning existing text."""

    def __init__(self, events: list[tuple[object, ...]]) -> None:
        self._events = events

    def render(self, serialized_report: object) -> str:
        """Record the exact plain serialized object received."""
        self._events.append(("markdown_render", serialized_report))
        return "markdown text"


class _HtmlRenderer:
    """Record HTML rendering invocation while returning existing text."""

    def __init__(self, events: list[tuple[object, ...]]) -> None:
        self._events = events

    def render(self, serialized_report: object) -> str:
        """Record the exact plain serialized object received."""
        self._events.append(("html_render", serialized_report))
        return "html text"


class _Writer:
    """Record exact rendered text and destination passed to persistence."""

    def __init__(self, events: list[tuple[object, ...]]) -> None:
        self._events = events

    def write(self, content: str, destination: Path) -> None:
        """Record the exact text and path without writing a file."""
        self._events.append(("write", content, destination))
