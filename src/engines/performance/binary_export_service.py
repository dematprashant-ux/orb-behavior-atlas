"""Dependency-injected orchestration for PDF and ZIP binary report exports."""

from dataclasses import dataclass
from pathlib import Path

from src.engines.performance.interfaces import (
    BinaryReportWriter,
    HtmlReportRenderer,
    JsonReportExporter,
    MarkdownReportRenderer,
    PdfReportRenderer,
    ReportBundleBuilder,
    ReportSerializer,
)
from src.engines.performance.models import BacktestReport

__all__ = ["StandardBinaryReportExportService"]


@dataclass(frozen=True, slots=True)
class StandardBinaryReportExportService:
    """Coordinate injected binary export collaborators without report processing."""

    serializer: ReportSerializer
    json_exporter: JsonReportExporter
    markdown_renderer: MarkdownReportRenderer
    html_renderer: HtmlReportRenderer
    pdf_renderer: PdfReportRenderer
    bundle_builder: ReportBundleBuilder
    binary_writer: BinaryReportWriter

    def __post_init__(self) -> None:
        """Require every collaborator without structural inspection or I/O."""
        dependencies = (
            (self.serializer, "serializer"),
            (self.json_exporter, "json_exporter"),
            (self.markdown_renderer, "markdown_renderer"),
            (self.html_renderer, "html_renderer"),
            (self.pdf_renderer, "pdf_renderer"),
            (self.bundle_builder, "bundle_builder"),
            (self.binary_writer, "binary_writer"),
        )
        for dependency, name in dependencies:
            if dependency is None:
                raise TypeError(f"{name} must not be None.")

    def export_pdf(self, report: BacktestReport, destination: Path) -> None:
        """Serialize, render PDF bytes, and write through injected collaborators."""
        serialized_report = self.serializer.serialize(report)
        content = self.pdf_renderer.render(serialized_report)
        self.binary_writer.write(content, destination)

    def export_bundle(self, report: BacktestReport, destination: Path) -> None:
        """Build fixed report artifacts and persist their bundled bytes by injection."""
        serialized_report = self.serializer.serialize(report)
        artifacts = {
            "report.json": self.json_exporter.export(serialized_report),
            "report.md": self.markdown_renderer.render(serialized_report),
            "report.html": self.html_renderer.render(serialized_report),
            "report.pdf": self.pdf_renderer.render(serialized_report),
        }
        content = self.bundle_builder.build(artifacts)
        self.binary_writer.write(content, destination)
