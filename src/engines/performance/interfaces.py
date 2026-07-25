"""Pure Performance Analytics protocol boundary without an implementation."""

from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

from src.engines.execution.models import CompletedTrade
from src.engines.performance.models import (
    DrawdownSummary,
    BacktestReport,
    EquityCurve,
    PerformanceContext,
    PerformanceMetrics,
    PerformanceReport,
    PnLSummary,
    RiskAdjustedMetrics,
)

__all__ = [
    "EquityCurveBuilder",
    "DrawdownAnalyzer",
    "PerformanceAnalyzer",
    "PerformanceEngine",
    "PnLEngine",
    "RiskMetricsAnalyzer",
    "ReportSerializer",
    "JsonReportExporter",
    "MarkdownReportRenderer",
    "HtmlReportRenderer",
    "ReportWriter",
    "ReportExportService",
    "PdfReportRenderer",
    "ReportBundleBuilder",
]


class PerformanceEngine(Protocol):
    """Defines the pure contract for a future performance-analysis implementation."""

    def analyze(self, context: PerformanceContext) -> PerformanceReport:
        """Return a structural report without implying metric calculation."""


class PnLEngine(Protocol):
    """Defines the pure contract for deterministic realized-PnL calculation."""

    def calculate(self, trades: tuple[CompletedTrade, ...]) -> PnLSummary:
        """Return an immutable summary calculated only from explicit trade facts."""


class PerformanceAnalyzer(Protocol):
    """Defines pure aggregate analysis over an immutable realized-PnL summary."""

    def analyze(self, summary: PnLSummary) -> PerformanceMetrics:
        """Return deterministic non-portfolio performance metrics."""


class EquityCurveBuilder(Protocol):
    """Defines pure cumulative-equity construction from immutable realized PnL."""

    def build(self, summary: PnLSummary) -> EquityCurve:
        """Return an ordered immutable cumulative-realized-equity curve."""


class DrawdownAnalyzer(Protocol):
    """Defines pure absolute-drawdown analysis over immutable equity curves."""

    def analyze(self, curve: EquityCurve) -> DrawdownSummary:
        """Return ordered running peaks and absolute drawdowns."""


class RiskMetricsAnalyzer(Protocol):
    """Defines pure absolute-return-to-drawdown metric analysis."""

    def analyze(
        self,
        performance: PerformanceMetrics,
        drawdown: DrawdownSummary,
    ) -> RiskAdjustedMetrics:
        """Return zero-safe metrics from existing aggregate artifacts only."""


class ReportSerializer(Protocol):
    """Defines pure plain-data serialization of an immutable backtest report."""

    def serialize(self, report: BacktestReport) -> Mapping[str, object]:
        """Return deterministic in-memory data without rendering or I/O."""


class JsonReportExporter(Protocol):
    """Defines pure deterministic JSON export from plain report data."""

    def export(self, serialized_report: Mapping[str, object]) -> str:
        """Return compact stable-key JSON without rendering or file I/O."""


class MarkdownReportRenderer(Protocol):
    """Defines pure in-memory Markdown rendering from plain report data."""

    def render(self, serialized_report: Mapping[str, object]) -> str:
        """Return deterministic Markdown without file I/O or calculations."""


class HtmlReportRenderer(Protocol):
    """Defines pure standalone HTML rendering from plain report data."""

    def render(self, serialized_report: Mapping[str, object]) -> str:
        """Return deterministic HTML without external resources or file I/O."""


class ReportWriter(Protocol):
    """Defines persistence of already-rendered text without report knowledge."""

    def write(self, content: str, destination: Path) -> None:
        """Persist exact UTF-8 text content to one destination path."""


class ReportExportService(Protocol):
    """Defines orchestration of existing report export collaborators only."""

    def export_json(self, report: BacktestReport, destination: Path) -> None:
        """Serialize, JSON-export, and write one report through injected objects."""

    def export_markdown(self, report: BacktestReport, destination: Path) -> None:
        """Serialize, Markdown-render, and write one report through injection."""

    def export_html(self, report: BacktestReport, destination: Path) -> None:
        """Serialize, HTML-render, and write one report through injection."""


class PdfReportRenderer(Protocol):
    """Defines pure in-memory PDF rendering from plain report data."""

    def render(self, serialized_report: Mapping[str, object]) -> bytes:
        """Return a complete deterministic PDF without file I/O."""


class ReportBundleBuilder(Protocol):
    """Defines deterministic in-memory ZIP creation from report artifacts."""

    def build(self, artifacts: Mapping[str, str | bytes]) -> bytes:
        """Return a complete ZIP archive without report processing or file I/O."""
