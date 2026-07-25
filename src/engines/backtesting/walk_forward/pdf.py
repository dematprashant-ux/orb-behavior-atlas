"""Deterministic in-memory PDF presentation for walk-forward report data."""

from collections.abc import Mapping
from dataclasses import dataclass
from html import escape
from io import BytesIO

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.engines.backtesting.walk_forward.rendering import _validate, _value

__all__ = ["StandardWalkForwardPdfRenderer"]


@dataclass(frozen=True, slots=True)
class StandardWalkForwardPdfRenderer:
    """Render serialized walk-forward plain data to deterministic PDF bytes."""

    def render(self, serialized_report: Mapping[str, object]) -> bytes:
        """Return a complete PDF without file I/O or generated timestamps."""
        summary, iterations = _validate(serialized_report)
        styles = _styles()
        story: list[object] = [Paragraph("Walk-Forward Report", styles["Title"])]
        story.extend(_section("Summary", _summary_rows(summary), styles))
        story.extend(_section("Iterations", _iteration_rows(iterations), styles))
        source = BytesIO()
        document = SimpleDocTemplate(
            source,
            pagesize=A4,
            leftMargin=16 * mm,
            rightMargin=16 * mm,
            topMargin=16 * mm,
            bottomMargin=16 * mm,
            invariant=1,
            pageCompression=0,
        )
        document.build(story)
        return _stable_pdf(source.getvalue())


def _summary_rows(values: Mapping[str, object]) -> list[list[str]]:
    """Return fixed-order structural rows from existing serialized values."""
    return [
        ["Metric", "Value"],
        ["Total Windows", _value(values, "total_windows")],
        ["Completed Iterations", _value(values, "completed_iterations")],
        ["Earliest Training Start", _value(values, "earliest_training_start")],
        ["Latest Validation End", _value(values, "latest_validation_end")],
    ]


def _iteration_rows(values: list[Mapping[str, object]]) -> list[list[str]]:
    """Return iteration rows in serializer order without any recalculation."""
    rows = [["Window", "Selection", "Training", "Validation"]]
    rows.extend(
        [
            _value(item, "window_index"),
            _value(item, "selection_id"),
            _value(item, "training_observation_count"),
            _value(item, "validation_observation_count"),
        ]
        for item in values
    )
    return rows


def _section(
    title: str,
    rows: list[list[str]],
    styles: Mapping[str, ParagraphStyle],
) -> list[object]:
    """Build one readable heading and stable table from supplied plain rows."""
    table = Table(
        [[Paragraph(escape(value), styles["BodyText"]) for value in row] for row in rows],
        repeatRows=1,
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F0F4F8")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#BCCCDC")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return [Spacer(1, 4 * mm), Paragraph(title, styles["Heading2"]), table]


def _styles() -> dict[str, ParagraphStyle]:
    """Return deterministic local PDF styles without external assets."""
    styles = getSampleStyleSheet()
    return {
        "Title": styles["Title"],
        "Heading2": styles["Heading2"],
        "BodyText": styles["BodyText"],
    }


def _stable_pdf(pdf_bytes: bytes) -> bytes:
    """Strip unstable PDF metadata while preserving visible document content."""
    reader = PdfReader(BytesIO(pdf_bytes))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.add_metadata({"/Title": "Walk-Forward Report", "/Producer": "ORB Behavior Atlas"})
    output = BytesIO()
    writer.write(output)
    return output.getvalue()
