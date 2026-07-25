"""Dependency-injected orchestration of existing report export components."""

from dataclasses import dataclass
from pathlib import Path

from src.engines.performance.interfaces import (
    HtmlReportRenderer,
    JsonReportExporter,
    MarkdownReportRenderer,
    ReportSerializer,
    ReportWriter,
)
from src.engines.performance.models import BacktestReport

__all__ = ["StandardReportExportService"]


@dataclass(frozen=True, slots=True)
class StandardReportExportService:
    """Coordinate injected serialization, text production, and writing only."""

    serializer: ReportSerializer
    json_exporter: JsonReportExporter
    markdown_renderer: MarkdownReportRenderer
    html_renderer: HtmlReportRenderer
    writer: ReportWriter

    def __post_init__(self) -> None:
        """Require all collaborators without structural inspection or I/O."""
        dependencies = (
            (self.serializer, "serializer"),
            (self.json_exporter, "json_exporter"),
            (self.markdown_renderer, "markdown_renderer"),
            (self.html_renderer, "html_renderer"),
            (self.writer, "writer"),
        )
        for dependency, name in dependencies:
            if dependency is None:
                raise TypeError(f"{name} must not be None.")

    def export_json(self, report: BacktestReport, destination: Path) -> None:
        """Serialize, JSON-export, and write through injected collaborators.

        No report facts are inspected or transformed by this service.
        """
        serialized_report = self.serializer.serialize(report)
        content = self.json_exporter.export(serialized_report)
        self.writer.write(content, destination)

    def export_markdown(self, report: BacktestReport, destination: Path) -> None:
        """Serialize, Markdown-render, and write through injected collaborators.

        No report facts are inspected or transformed by this service.
        """
        serialized_report = self.serializer.serialize(report)
        content = self.markdown_renderer.render(serialized_report)
        self.writer.write(content, destination)

    def export_html(self, report: BacktestReport, destination: Path) -> None:
        """Serialize, HTML-render, and write through injected collaborators.

        No report facts are inspected or transformed by this service.
        """
        serialized_report = self.serializer.serialize(report)
        content = self.html_renderer.render(serialized_report)
        self.writer.write(content, destination)
