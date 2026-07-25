"""Deterministic in-memory Markdown rendering for plain backtest-report data."""

from collections.abc import Mapping
from dataclasses import dataclass

__all__ = ["StandardMarkdownReportRenderer"]

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


@dataclass(frozen=True, slots=True)
class StandardMarkdownReportRenderer:
    """Render plain report mappings as stable Markdown without side effects."""

    def render(self, serialized_report: Mapping[str, object]) -> str:
        """Return deterministic Markdown for required plain serialized sections.

        Args:
            serialized_report: Plain data produced by ``DictionaryReportSerializer``.

        Returns:
            UTF-8-compatible Markdown terminated by exactly one newline.

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
            "# Backtest Report",
            "",
            "| Report Mode |",
            "| --- |",
            f"| {report_mode} |",
            "",
            "## Performance Metrics",
            "",
        ]
        lines.extend(_render_metric_table(performance, _PERFORMANCE_METRICS))
        lines.extend(["", "## Risk-Adjusted Metrics", ""])
        lines.extend(_render_metric_table(risk, _RISK_METRICS))
        lines.extend(["", "## Equity Curve", ""])
        lines.extend(_render_equity_curve(equity_curve))
        lines.extend(["", "## Drawdown Summary", ""])
        lines.extend(_render_drawdown_summary(drawdown_summary))
        return "\n".join(lines).rstrip("\n") + "\n"


def _render_metric_table(
    values: Mapping[str, object],
    fields: tuple[tuple[str, str], ...],
) -> list[str]:
    """Render ordered labels and existing scalar values into a Markdown table."""
    lines = ["| Metric | Value |", "| --- | --- |"]
    for field_name, label in fields:
        lines.append(
            f"| {label} | {_format_value(_require_field(values, field_name))} |"
        )
    return lines


def _render_equity_curve(values: Mapping[str, object]) -> list[str]:
    """Render existing final equity and ordered plain equity-point data."""
    points = _require_list(_require_field(values, "points"), "equity_curve.points")
    lines = [
        "| Final Equity |",
        "| --- |",
        f"| {_format_value(_require_field(values, 'final_equity'))} |",
        "",
        "| Source Trade PnL | Cumulative Realized PnL |",
        "| --- | --- |",
    ]
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
            "| "
            f"{realized_pnl} | "
            f"{cumulative_pnl} |"
        )
    return lines


def _render_drawdown_summary(values: Mapping[str, object]) -> list[str]:
    """Render existing maximum drawdown and ordered plain drawdown-point data."""
    points = _require_list(
        _require_field(values, "points"),
        "drawdown_summary.points",
    )
    lines = [
        "| Maximum Drawdown |",
        "| --- |",
        f"| {_format_value(_require_field(values, 'maximum_drawdown'))} |",
        "",
        "| Source Trade PnL | Cumulative Realized PnL | Running Peak | Drawdown |",
        "| --- | --- | --- | --- |",
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
        realized_pnl = _format_value(_require_field(trade_pnl, "realized_pnl"))
        cumulative_pnl = _format_value(
            _require_field(equity_point, "cumulative_realized_pnl")
        )
        running_peak = _format_value(_require_field(point_values, "running_peak"))
        drawdown = _format_value(_require_field(point_values, "drawdown"))
        lines.append(
            "| "
            f"{realized_pnl} | "
            f"{cumulative_pnl} | "
            f"{running_peak} | "
            f"{drawdown} |"
        )
    return lines


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
    """Render one supported plain scalar without rounding or Markdown decoration."""
    if value is None:
        return "N/A"
    if isinstance(value, (str, bool, int, float)):
        return str(value)
    raise TypeError("serialized scalar values must be plain values.")
