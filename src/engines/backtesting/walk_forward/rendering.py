"""Deterministic in-memory Markdown and HTML walk-forward presentation."""

from collections.abc import Mapping
from dataclasses import dataclass
from html import escape

__all__ = [
    "StandardWalkForwardHtmlRenderer",
    "StandardWalkForwardMarkdownRenderer",
]


@dataclass(frozen=True, slots=True)
class StandardWalkForwardMarkdownRenderer:
    """Render serialized walk-forward data as deterministic Markdown."""

    def render(self, serialized_report: Mapping[str, object]) -> str:
        """Return a newline-terminated representation without calculations."""
        summary, iterations = _validate(serialized_report)
        lines = ["# Walk-Forward Report", "", "## Summary", ""]
        lines.extend(_markdown_summary(summary))
        lines.extend(["", "## Iterations", ""])
        lines.extend(_markdown_iterations(iterations))
        return "\n".join(lines).rstrip("\n") + "\n"


@dataclass(frozen=True, slots=True)
class StandardWalkForwardHtmlRenderer:
    """Render serialized walk-forward data as deterministic standalone HTML."""

    def render(self, serialized_report: Mapping[str, object]) -> str:
        """Return an escaped UTF-8 HTML document without external resources."""
        summary, iterations = _validate(serialized_report)
        lines = [
            "<!DOCTYPE html>",
            '<html lang="en">',
            "<head>",
            '  <meta charset="utf-8">',
            "  <title>Walk-Forward Report</title>",
            "</head>",
            "<body>",
            "  <main>",
            "    <h1>Walk-Forward Report</h1>",
            "    <section><h2>Summary</h2>",
            "      <table><thead><tr><th>Metric</th><th>Value</th></tr></thead>",
            "      <tbody>",
        ]
        for label, value in _summary_items(summary):
            lines.append(f"        <tr><td>{label}</td><td>{escape(value)}</td></tr>")
        lines.extend(
            [
                "      </tbody></table>",
                "    </section>",
                "    <section><h2>Iterations</h2>",
                "      <table><thead><tr><th>Window</th><th>Selection</th>"
                "<th>Training Observations</th><th>Validation Observations</th>"
                "</tr></thead>",
                "      <tbody>",
            ]
        )
        for iteration in iterations:
            lines.append(
                "        <tr>"
                f"<td>{escape(_value(iteration, 'window_index'))}</td>"
                f"<td>{escape(_value(iteration, 'selection_id'))}</td>"
                f"<td>{escape(_value(iteration, 'training_observation_count'))}</td>"
                f"<td>{escape(_value(iteration, 'validation_observation_count'))}</td>"
                "</tr>"
            )
        lines.extend(["      </tbody></table>", "    </section>", "  </main>", "</body>", "</html>"])
        return "\n".join(lines).rstrip("\n") + "\n"


def _validate(
    serialized_report: Mapping[str, object],
) -> tuple[Mapping[str, object], list[Mapping[str, object]]]:
    """Validate only the serializer-shaped plain-data structure."""
    if not isinstance(serialized_report, Mapping):
        raise TypeError("serialized_report must be a Mapping.")
    if serialized_report.get("report_type") != "walk_forward":
        raise ValueError("report_type must be 'walk_forward'.")
    summary = _mapping(serialized_report.get("summary"), "summary")
    iterations_value = serialized_report.get("iterations")
    if not isinstance(iterations_value, list):
        raise TypeError("iterations must be a list.")
    iterations = [
        _mapping(iteration, f"iterations[{index}]")
        for index, iteration in enumerate(iterations_value)
    ]
    for name in (
        "total_windows",
        "completed_iterations",
        "earliest_training_start",
        "latest_validation_end",
    ):
        _value(summary, name)
    return summary, iterations


def _markdown_summary(summary: Mapping[str, object]) -> list[str]:
    """Return the stable summary table from existing plain values."""
    lines = ["| Metric | Value |", "| --- | --- |"]
    lines.extend(f"| {label} | {value} |" for label, value in _summary_items(summary))
    return lines


def _markdown_iterations(iterations: list[Mapping[str, object]]) -> list[str]:
    """Return an ordered iteration table without reconstructing model objects."""
    lines = [
        "| Window | Selection | Training Observations | Validation Observations |",
        "| --- | --- | --- | --- |",
    ]
    for iteration in iterations:
        lines.append(
            "| "
            f"{_value(iteration, 'window_index')} | "
            f"{_value(iteration, 'selection_id')} | "
            f"{_value(iteration, 'training_observation_count')} | "
            f"{_value(iteration, 'validation_observation_count')} |"
        )
    return lines


def _summary_items(summary: Mapping[str, object]) -> tuple[tuple[str, str], ...]:
    """Return the fixed human-readable structural summary item order."""
    return (
        ("Total Windows", _value(summary, "total_windows")),
        ("Completed Iterations", _value(summary, "completed_iterations")),
        ("Earliest Training Start", _value(summary, "earliest_training_start")),
        ("Latest Validation End", _value(summary, "latest_validation_end")),
    )


def _mapping(value: object, name: str) -> Mapping[str, object]:
    """Require one plain mapping section."""
    if not isinstance(value, Mapping):
        raise TypeError(f"{name} must be a Mapping.")
    return value


def _value(values: Mapping[str, object], name: str) -> str:
    """Return one faithful plain scalar without formatting or calculation."""
    if name not in values:
        raise ValueError(f"missing required field: {name}.")
    value = values[name]
    if value is None:
        return "N/A"
    if not isinstance(value, (str, int)):
        raise TypeError(f"{name} must be a plain scalar.")
    return str(value)
