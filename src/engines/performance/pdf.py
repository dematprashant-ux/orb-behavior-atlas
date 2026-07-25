"""Deterministic in-memory PDF rendering for plain backtest-report data."""

from collections.abc import Mapping
from dataclasses import dataclass
from html import escape
from io import BytesIO
from pathlib import Path

import reportlab
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

__all__ = ["StandardPdfReportRenderer"]

_FONT_NAME = "ORB-Vera"
_FONT_PATH = Path(reportlab.__file__).parent / "fonts" / "Vera.ttf"
_PERFORMANCE_METRICS = (
    ("total_trades", "Total Trades"),
    ("winning_trades", "Winning Trades"),
    ("losing_trades", "Losing Trades"),
    ("flat_trades", "Flat Trades"),
    ("gross_profit", "Gross Profit"),
    ("gross_loss", "Gross Loss"),
    ("net_profit", "Net Profit"),
    ("win_rate", "Win Rate"),
    ("loss_rate", "Loss Rate"),
    ("flat_rate", "Flat Rate"),
    ("average_trade_pnl", "Average Trade PnL"),
    ("average_winning_trade", "Average Winning Trade"),
    ("average_losing_trade", "Average Losing Trade"),
    ("profit_factor", "Profit Factor"),
    ("expectancy", "Expectancy"),
)
_RISK_METRICS = (
    ("recovery_factor", "Recovery Factor"),
    ("return_over_drawdown", "Return Over Drawdown"),
)
_PORTFOLIO_METRICS = (
    ("initial_equity", "Initial Equity"),
    ("final_equity", "Final Equity"),
    ("absolute_return", "Absolute Return"),
    ("total_return", "Total Return"),
    ("maximum_equity", "Maximum Equity"),
    ("minimum_equity", "Minimum Equity"),
    ("equity_point_count", "Equity Point Count"),
)


@dataclass(frozen=True, slots=True)
class StandardPdfReportRenderer:
    """Render plain report mappings as deterministic in-memory PDF bytes."""

    def render(self, serialized_report: Mapping[str, object]) -> bytes:
        """Return one complete PDF from required plain serialized sections.

        Args:
            serialized_report: Plain data produced by ``DictionaryReportSerializer``.

        Returns:
            A standalone PDF document with no creation or modification timestamp.

        Raises:
            TypeError: If the report or a required section has an invalid shape.
            ValueError: If a required section or field is missing.
        """
        report = _require_mapping(serialized_report, "serialized_report")
        if report.get("report_type") == "portfolio":
            return _render_portfolio_pdf(report)
        report_mode = _require_report_mode(report)
        performance = _require_section(report, "performance_metrics")
        risk = _require_section(report, "risk_adjusted_metrics")
        equity_curve = _require_section(report, "equity_curve")
        drawdown_summary = _require_section(report, "drawdown_summary")
        _ensure_font_registered()

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
        story = _build_story(
            report_mode,
            performance,
            risk,
            equity_curve,
            drawdown_summary,
        )
        document.build(story)
        return _rewrite_without_timestamps(source.getvalue())


def _render_portfolio_pdf(report: Mapping[str, object]) -> bytes:
    """Render portfolio plain data through the existing deterministic PDF stack."""
    performance = _require_section(report, "performance_metrics")
    equity_curve = _require_section(report, "equity_curve")
    drawdown_summary = _require_section(report, "drawdown_summary")
    _ensure_font_registered()
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
    styles = _styles()
    story: list[object] = [Paragraph("Portfolio Report", styles["title"])]
    story.extend(
        _section_flowables(
            "Performance Metrics",
            performance,
            _PORTFOLIO_METRICS,
            styles,
        )
    )
    story.extend(_portfolio_equity_flowables(equity_curve, styles))
    story.extend(_portfolio_drawdown_flowables(drawdown_summary, styles))
    document.build(story)
    return _rewrite_without_timestamps(source.getvalue())


def _portfolio_equity_flowables(
    values: Mapping[str, object],
    styles: Mapping[str, ParagraphStyle],
) -> list[object]:
    """Build existing portfolio equity point tables without valuation logic."""
    points = _require_list(_require_field(values, "points"), "equity_curve.points")
    rows = [
        [
            _paragraph("Timestamp", styles),
            _paragraph("Cash", styles),
            _paragraph("Position Value", styles),
            _paragraph("Total Equity", styles),
        ]
    ]
    for index, point in enumerate(points):
        data = _require_mapping(point, f"equity_curve.points[{index}]")
        rows.append(
            [
                _paragraph(_format_value(_require_field(data, "timestamp")), styles),
                _paragraph(_format_value(_require_field(data, "cash")), styles),
                _paragraph(
                    _format_value(_require_field(data, "position_value")),
                    styles,
                ),
                _paragraph(_format_value(_require_field(data, "total_equity")), styles),
            ]
        )
    return _portfolio_value_flowables(
        "Equity Curve",
        "Final Equity",
        _require_field(values, "final_equity"),
        rows,
        (60 * mm, 35 * mm, 40 * mm, 40 * mm),
        styles,
    )


def _portfolio_drawdown_flowables(
    values: Mapping[str, object],
    styles: Mapping[str, ParagraphStyle],
) -> list[object]:
    """Build existing portfolio drawdown tables without recalculating drawdown."""
    points = _require_list(
        _require_field(values, "points"),
        "drawdown_summary.points",
    )
    rows = [
        [
            _paragraph("Timestamp", styles),
            _paragraph("Running Peak", styles),
            _paragraph("Drawdown", styles),
        ]
    ]
    for index, point in enumerate(points):
        data = _require_mapping(point, f"drawdown_summary.points[{index}]")
        rows.append(
            [
                _paragraph(_format_value(_require_field(data, "timestamp")), styles),
                _paragraph(_format_value(_require_field(data, "running_peak")), styles),
                _paragraph(_format_value(_require_field(data, "drawdown")), styles),
            ]
        )
    return _portfolio_value_flowables(
        "Drawdown Summary",
        "Maximum Drawdown",
        _require_field(values, "maximum_drawdown"),
        rows,
        (62 * mm, 56 * mm, 56 * mm),
        styles,
    )


def _portfolio_value_flowables(
    title: str,
    summary_label: str,
    summary_value: object,
    rows: list[list[Paragraph]],
    widths: tuple[float, ...],
    styles: Mapping[str, ParagraphStyle],
) -> list[object]:
    """Build one summary and existing plain-data table in stable row order."""
    return [
        Spacer(1, 4 * mm),
        Paragraph(title, styles["section"]),
        _table(
            [
                [_paragraph(summary_label, styles)],
                [_paragraph(_format_value(summary_value), styles)],
            ],
            (175 * mm,),
        ),
        Spacer(1, 2 * mm),
        _table(rows, widths),
    ]


def _build_story(
    report_mode: str,
    performance: Mapping[str, object],
    risk: Mapping[str, object],
    equity_curve: Mapping[str, object],
    drawdown_summary: Mapping[str, object],
) -> list[object]:
    """Build ordered PDF flowables from existing plain-data report facts."""
    styles = _styles()
    story: list[object] = [
        Paragraph("Backtest Report", styles["title"]),
        Spacer(1, 2 * mm),
        _paragraph(f"Report Mode: {report_mode}", styles),
    ]
    story.extend(
        _section_flowables(
            "Performance Metrics",
            performance,
            _PERFORMANCE_METRICS,
            styles,
        )
    )
    story.extend(
        _section_flowables(
            "Risk-Adjusted Metrics",
            risk,
            _RISK_METRICS,
            styles,
        )
    )
    story.extend(_equity_flowables(equity_curve, styles))
    story.extend(_drawdown_flowables(drawdown_summary, styles))
    return story


def _section_flowables(
    title: str,
    values: Mapping[str, object],
    fields: tuple[tuple[str, str], ...],
    styles: Mapping[str, ParagraphStyle],
) -> list[object]:
    """Build one heading and labeled metric table in stable source-field order."""
    rows = [[_paragraph("Metric", styles), _paragraph("Value", styles)]]
    for field_name, label in fields:
        rows.append(
            [
                _paragraph(label, styles),
                _paragraph(
                    _format_value(_require_field(values, field_name)),
                    styles,
                ),
            ]
        )
    return [
        Spacer(1, 4 * mm),
        Paragraph(title, styles["section"]),
        _table(rows, (70 * mm, 105 * mm)),
    ]


def _equity_flowables(
    values: Mapping[str, object],
    styles: Mapping[str, ParagraphStyle],
) -> list[object]:
    """Build ordered final-equity and equity-point tables without calculations."""
    points = _require_list(
        _require_field(values, "points"),
        "equity_curve.points",
    )
    final_equity = _format_value(_require_field(values, "final_equity"))
    summary_rows = [
        [_paragraph("Final Equity", styles)],
        [_paragraph(final_equity, styles)],
    ]
    point_rows = [
        [
            _paragraph("Source Trade PnL", styles),
            _paragraph("Cumulative Realized PnL", styles),
        ]
    ]
    for index, point in enumerate(points):
        point_values = _require_mapping(point, f"equity_curve.points[{index}]")
        trade_pnl = _require_mapping(
            _require_field(point_values, "source_trade_pnl"),
            f"equity_curve.points[{index}].source_trade_pnl",
        )
        point_rows.append(
            [
                _paragraph(
                    _format_value(_require_field(trade_pnl, "realized_pnl")),
                    styles,
                ),
                _paragraph(
                    _format_value(
                        _require_field(point_values, "cumulative_realized_pnl")
                    ),
                    styles,
                ),
            ]
        )
    return [
        Spacer(1, 4 * mm),
        Paragraph("Equity Curve", styles["section"]),
        _table(summary_rows, (175 * mm,)),
        Spacer(1, 2 * mm),
        _table(point_rows, (70 * mm, 105 * mm)),
    ]


def _drawdown_flowables(
    values: Mapping[str, object],
    styles: Mapping[str, ParagraphStyle],
) -> list[object]:
    """Build ordered maximum-drawdown and drawdown-point tables from plain data."""
    points = _require_list(
        _require_field(values, "points"),
        "drawdown_summary.points",
    )
    maximum_drawdown = _format_value(_require_field(values, "maximum_drawdown"))
    summary_rows = [
        [_paragraph("Maximum Drawdown", styles)],
        [_paragraph(maximum_drawdown, styles)],
    ]
    point_rows = [
        [
            _paragraph("Source Trade PnL", styles),
            _paragraph("Cumulative Realized PnL", styles),
            _paragraph("Running Peak", styles),
            _paragraph("Drawdown", styles),
        ]
    ]
    for index, point in enumerate(points):
        point_values = _require_mapping(point, f"drawdown_summary.points[{index}]")
        equity_point = _require_mapping(
            _require_field(point_values, "source_equity_point"),
            f"drawdown_summary.points[{index}].source_equity_point",
        )
        trade_pnl = _require_mapping(
            _require_field(equity_point, "source_trade_pnl"),
            f"drawdown_summary.points[{index}].source_trade_pnl",
        )
        point_rows.append(
            [
                _paragraph(
                    _format_value(_require_field(trade_pnl, "realized_pnl")),
                    styles,
                ),
                _paragraph(
                    _format_value(
                        _require_field(equity_point, "cumulative_realized_pnl")
                    ),
                    styles,
                ),
                _paragraph(
                    _format_value(_require_field(point_values, "running_peak")),
                    styles,
                ),
                _paragraph(
                    _format_value(_require_field(point_values, "drawdown")),
                    styles,
                ),
            ]
        )
    return [
        Spacer(1, 4 * mm),
        Paragraph("Drawdown Summary", styles["section"]),
        _table(summary_rows, (175 * mm,)),
        Spacer(1, 2 * mm),
        _table(point_rows, (38 * mm, 58 * mm, 38 * mm, 41 * mm)),
    ]


def _styles() -> dict[str, ParagraphStyle]:
    """Return deterministic local styles using the embedded document font."""
    return {
        "title": ParagraphStyle(
            "orb-title",
            fontName=_FONT_NAME,
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#102A43"),
        ),
        "section": ParagraphStyle(
            "orb-section",
            fontName=_FONT_NAME,
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#102A43"),
        ),
        "cell": ParagraphStyle(
            "orb-cell",
            fontName=_FONT_NAME,
            fontSize=8,
            leading=10,
        ),
        "header": ParagraphStyle(
            "orb-header",
            fontName=_FONT_NAME,
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#102A43"),
        ),
    }


def _paragraph(text: str, styles: Mapping[str, ParagraphStyle]) -> Paragraph:
    """Return one safe text paragraph, using header style for static headings."""
    style = styles["header"] if text in _table_headers() else styles["cell"]
    return Paragraph(escape(text, quote=True), style)


def _table(rows: list[list[Paragraph]], widths: tuple[float, ...]) -> Table:
    """Return one readable deterministic table with a shaded first row."""
    table = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
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
    return table


def _table_headers() -> frozenset[str]:
    """Return static labels whose table cells receive the header text style."""
    return frozenset(
        {
            "Metric",
            "Value",
            "Final Equity",
            "Maximum Drawdown",
            "Source Trade PnL",
            "Cumulative Realized PnL",
            "Running Peak",
            "Drawdown",
        }
    )


def _ensure_font_registered() -> None:
    """Register the bundled Vera font once so PDF output embeds no external font."""
    try:
        pdfmetrics.getFont(_FONT_NAME)
    except KeyError:
        pdfmetrics.registerFont(TTFont(_FONT_NAME, str(_FONT_PATH)))


def _rewrite_without_timestamps(pdf_bytes: bytes) -> bytes:
    """Return deterministic PDF bytes with metadata restricted to stable values."""
    reader = PdfReader(BytesIO(pdf_bytes))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.add_metadata(
        {
            "/Title": "Backtest Report",
            "/Producer": "ORB Behavior Atlas",
        }
    )
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def _require_section(
    report: Mapping[str, object],
    section_name: str,
) -> Mapping[str, object]:
    """Return one required top-level plain-data mapping section."""
    return _require_mapping(_require_field(report, section_name), section_name)


def _require_report_mode(report: Mapping[str, object]) -> str:
    """Return one required serialized gross or net report-mode display value."""
    report_mode = _require_field(report, "report_mode")
    if report_mode == "gross":
        return "Gross"
    if report_mode == "net":
        return "Net"
    raise ValueError("report_mode must be 'gross' or 'net'.")


def _require_field(values: Mapping[str, object], field_name: str) -> object:
    """Return one required plain-data field without transforming it."""
    if field_name not in values:
        raise ValueError(f"missing required field: {field_name}.")
    return values[field_name]


def _require_mapping(value: object, field_name: str) -> Mapping[str, object]:
    """Require one mapping section in the serialized report structure."""
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a Mapping.")
    return value


def _require_list(value: object, field_name: str) -> list[object]:
    """Require one ordered list produced by the plain-data serializer."""
    if not isinstance(value, list):
        raise TypeError(f"{field_name} must be a list.")
    return value


def _format_value(value: object) -> str:
    """Return one faithful scalar display value without rounding or calculations."""
    if value is None:
        return "N/A"
    if isinstance(value, (str, bool, int, float)):
        return str(value)
    raise TypeError("serialized scalar values must be plain values.")
