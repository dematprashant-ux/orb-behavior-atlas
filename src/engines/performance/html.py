"""Deterministic standalone HTML rendering for plain backtest-report data."""

from collections.abc import Mapping
from dataclasses import dataclass
from html import escape

__all__ = ["StandardHtmlReportRenderer"]

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
_CSS = """body {
  color: #1f2933;
  font-family: Arial, sans-serif;
  line-height: 1.5;
  margin: 0 auto;
  max-width: 960px;
  padding: 2rem;
}
h1, h2 {
  color: #102a43;
}
section {
  margin-top: 2rem;
}
.table-wrap {
  overflow-x: auto;
}
table {
  border-collapse: collapse;
  margin-top: 0.75rem;
  width: 100%;
}
th, td {
  border: 1px solid #bcccdc;
  padding: 0.5rem;
  text-align: left;
}
th {
  background: #f0f4f8;
}
@media print {
  body {
    margin: 0;
    max-width: none;
    padding: 0;
  }
  .table-wrap {
    overflow: visible;
  }
}"""


@dataclass(frozen=True, slots=True)
class StandardHtmlReportRenderer:
    """Render plain report mappings as standalone HTML without side effects."""

    def render(self, serialized_report: Mapping[str, object]) -> str:
        """Return deterministic standalone HTML for plain serialized sections.

        Args:
            serialized_report: Plain data produced by ``DictionaryReportSerializer``.

        Returns:
            A complete UTF-8-compatible HTML document with one trailing newline.

        Raises:
            TypeError: If the report or a required section has an invalid shape.
            ValueError: If a required section or field is missing.
        """
        report = _require_mapping(serialized_report, "serialized_report")
        report_mode = _require_report_mode(report)
        performance = _require_section(report, "performance_metrics")
        risk = _require_section(report, "risk_adjusted_metrics")
        equity_curve = _require_section(report, "equity_curve")
        drawdown_summary = _require_section(report, "drawdown_summary")

        lines = [
            "<!DOCTYPE html>",
            '<html lang="en">',
            "<head>",
            '  <meta charset="utf-8">',
            '  <meta name="viewport" content="width=device-width, initial-scale=1">',
            "  <title>Backtest Report</title>",
            "  <style>",
        ]
        lines.extend(f"{line}" for line in _CSS.splitlines())
        lines.extend(
            [
                "  </style>",
                "</head>",
                "<body>",
                "  <main>",
                "    <h1>Backtest Report</h1>",
                '    <section aria-labelledby="report-mode">',
                '      <h2 id="report-mode">Report Mode</h2>',
                f"      <p>{_format_value(report_mode)}</p>",
                "    </section>",
            ]
        )
        lines.extend(
            _render_metric_section(
                "Performance Metrics",
                performance,
                _PERFORMANCE_METRICS,
            )
        )
        lines.extend(
            _render_metric_section(
                "Risk-Adjusted Metrics",
                risk,
                _RISK_METRICS,
            )
        )
        lines.extend(_render_equity_section(equity_curve))
        lines.extend(_render_drawdown_section(drawdown_summary))
        lines.extend(["  </main>", "</body>", "</html>"])
        return "\n".join(lines).rstrip("\n") + "\n"


def _render_metric_section(
    title: str,
    values: Mapping[str, object],
    fields: tuple[tuple[str, str], ...],
) -> list[str]:
    """Render one labeled metric section in the required deterministic order."""
    section_id = title.lower().replace(" ", "-")
    lines = [
        f'    <section aria-labelledby="{section_id}">',
        f'      <h2 id="{section_id}">{title}</h2>',
        '      <div class="table-wrap">',
        "        <table>",
        "          <thead><tr><th scope=\"col\">Metric</th>"
        "<th scope=\"col\">Value</th></tr></thead>",
        "          <tbody>",
    ]
    for field_name, label in fields:
        value = _format_value(_require_field(values, field_name))
        lines.append(
            f"            <tr><th scope=\"row\">{label}</th><td>{value}</td></tr>"
        )
    lines.extend(
        [
            "          </tbody>",
            "        </table>",
            "      </div>",
            "    </section>",
        ]
    )
    return lines


def _render_equity_section(values: Mapping[str, object]) -> list[str]:
    """Render existing final equity and ordered plain equity-point data."""
    points = _require_list(
        _require_field(values, "points"),
        "equity_curve.points",
    )
    lines = [
        '    <section aria-labelledby="equity-curve">',
        '      <h2 id="equity-curve">Equity Curve</h2>',
    ]
    lines.extend(
        _single_value_table(
            "Final Equity",
            _require_field(values, "final_equity"),
        )
    )
    lines.extend(
        [
            '      <div class="table-wrap">',
            "        <table>",
            "          <thead><tr><th scope=\"col\">Source Trade PnL</th>"
            "<th scope=\"col\">Cumulative Realized PnL</th></tr></thead>",
            "          <tbody>",
        ]
    )
    for index, point in enumerate(points):
        point_values = _require_mapping(point, f"equity_curve.points[{index}]")
        trade_pnl = _require_mapping(
            _require_field(point_values, "source_trade_pnl"),
            f"equity_curve.points[{index}].source_trade_pnl",
        )
        realized_pnl = _format_value(_require_field(trade_pnl, "realized_pnl"))
        cumulative_pnl = _format_value(
            _require_field(point_values, "cumulative_realized_pnl")
        )
        lines.append(
            "            <tr>"
            f"<td>{realized_pnl}</td>"
            f"<td>{cumulative_pnl}</td>"
            "</tr>"
        )
    lines.extend(
        [
            "          </tbody>",
            "        </table>",
            "      </div>",
            "    </section>",
        ]
    )
    return lines


def _render_drawdown_section(values: Mapping[str, object]) -> list[str]:
    """Render existing maximum drawdown and ordered plain drawdown-point data."""
    points = _require_list(
        _require_field(values, "points"),
        "drawdown_summary.points",
    )
    lines = [
        '    <section aria-labelledby="drawdown-summary">',
        '      <h2 id="drawdown-summary">Drawdown Summary</h2>',
    ]
    lines.extend(
        _single_value_table(
            "Maximum Drawdown",
            _require_field(values, "maximum_drawdown"),
        )
    )
    lines.extend(
        [
            '      <div class="table-wrap">',
            "        <table>",
            "          <thead><tr><th scope=\"col\">Source Trade PnL</th>"
            "<th scope=\"col\">Cumulative Realized PnL</th>"
            "<th scope=\"col\">Running Peak</th>"
            "<th scope=\"col\">Drawdown</th></tr></thead>",
            "          <tbody>",
        ]
    )
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
        realized_pnl = _format_value(_require_field(trade_pnl, "realized_pnl"))
        cumulative_pnl = _format_value(
            _require_field(equity_point, "cumulative_realized_pnl")
        )
        running_peak = _format_value(_require_field(point_values, "running_peak"))
        drawdown = _format_value(_require_field(point_values, "drawdown"))
        lines.append(
            "            <tr>"
            f"<td>{realized_pnl}</td>"
            f"<td>{cumulative_pnl}</td>"
            f"<td>{running_peak}</td>"
            f"<td>{drawdown}</td>"
            "</tr>"
        )
    lines.extend(
        [
            "          </tbody>",
            "        </table>",
            "      </div>",
            "    </section>",
        ]
    )
    return lines


def _single_value_table(label: str, value: object) -> list[str]:
    """Render one existing scalar fact without calculating or formatting it."""
    return [
        '      <div class="table-wrap">',
        "        <table>",
        f"          <thead><tr><th scope=\"col\">{label}</th></tr></thead>",
        f"          <tbody><tr><td>{_format_value(value)}</td></tr></tbody>",
        "        </table>",
        "      </div>",
    ]


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
    """Escape one supported plain scalar without rounding or markup insertion."""
    if value is None:
        return "N/A"
    if isinstance(value, (str, bool, int, float)):
        return escape(str(value), quote=True)
    raise TypeError("serialized scalar values must be plain values.")
