"""Contract tests for deterministic HTML optimization summary rendering."""

from unittest import TestCase
from unittest.mock import patch

from src.engines.backtesting import (
    HtmlOptimizationRunSummaryReportRenderer,
    MarkdownOptimizationRunSummaryReportRenderer,
    OptimizationRunSummaries,
    OptimizationRunSummary,
    OptimizationRunSummaryAggregate,
    OptimizationRunSummaryAnalysis,
    OptimizationRunSummaryRenderedReport,
    OptimizationRunSummaryReport,
    OptimizationRunSummaryReportRenderer,
    OptimizationRunSummaryRates,
    OptimizationStrategyMetadata,
    OptimizationTerminationReason,
    PlainTextOptimizationRunSummaryReportRenderer,
)


class HtmlOptimizationRunSummaryReportRendererTests(TestCase):
    """Verify HTML rendering reads only retained scalar analysis values."""

    def test_renderer_is_stateless_and_satisfies_the_existing_protocol(self) -> None:
        renderer: OptimizationRunSummaryReportRenderer[str] = (
            HtmlOptimizationRunSummaryReportRenderer()
        )

        self.assertEqual(renderer, HtmlOptimizationRunSummaryReportRenderer())
        self.assertEqual(
            repr(renderer),
            repr(HtmlOptimizationRunSummaryReportRenderer()),
        )
        self.assertEqual(HtmlOptimizationRunSummaryReportRenderer.__slots__, ())

    def test_rendering_uses_exact_semantic_structure_and_raw_values(self) -> None:
        report = _report(
            (
                _summary("grid", 3, 3, 2, _EXHAUSTED),
                _summary("random", 1, 4, 1, _BUDGET),
            )
        )

        rendered = HtmlOptimizationRunSummaryReportRenderer().render(report)

        self.assertIsInstance(rendered, OptimizationRunSummaryRenderedReport)
        self.assertIsInstance(rendered.payload, str)
        self.assertEqual(
            rendered.payload.split("\n"),
            _expected_lines(
                "2",
                "4",
                "7",
                "3",
                "1",
                "1",
                "0.5714285714285714",
                "0.42857142857142855",
                "0.5",
                "0.5",
            ),
        )
        self.assertFalse(rendered.payload.startswith("\n"))
        self.assertFalse(rendered.payload.endswith("\n"))
        self.assertNotIn("\t", rendered.payload)
        self.assertNotIn("%", rendered.payload)
        self.assertNotIn("<!DOCTYPE", rendered.payload)
        self.assertNotIn("<html", rendered.payload)
        self.assertNotIn("<head", rendered.payload)
        self.assertNotIn("<body", rendered.payload)
        self.assertTrue(
            all(line == line.rstrip() for line in rendered.payload.split("\n"))
        )

    def test_empty_report_renders_complete_zero_value_fragment(self) -> None:
        rendered = HtmlOptimizationRunSummaryReportRenderer().render(_report(()))

        self.assertEqual(
            rendered.payload.split("\n"),
            _expected_lines("0", "0", "0", "0", "0", "0", "0.0", "0.0", "0.0", "0.0"),
        )

    def test_rendering_does_not_recalculate_traverse_or_call_other_renderers(
        self,
    ) -> None:
        summaries = OptimizationRunSummaries((_summary("grid", 1, 1, 0, _EXHAUSTED),))
        report = _report_from_summaries(summaries)

        with patch.object(
            OptimizationRunSummaries,
            "__iter__",
            side_effect=AssertionError("summaries must not be traversed"),
        ), patch.object(
            OptimizationRunSummaryAggregate,
            "from_summaries",
            side_effect=AssertionError("aggregate must not be recalculated"),
        ), patch.object(
            OptimizationRunSummaryRates,
            "from_aggregate",
            side_effect=AssertionError("rates must not be recalculated"),
        ), patch.object(
            PlainTextOptimizationRunSummaryReportRenderer,
            "render",
            side_effect=AssertionError("plain-text renderer must not be called"),
        ), patch.object(
            MarkdownOptimizationRunSummaryReportRenderer,
            "render",
            side_effect=AssertionError("Markdown renderer must not be called"),
        ):
            first = HtmlOptimizationRunSummaryReportRenderer().render(report)
            second = HtmlOptimizationRunSummaryReportRenderer().render(report)

        self.assertEqual(first, second)
        self.assertEqual(report.analysis.aggregate.run_count, 1)
        self.assertEqual(report.analysis.rates.candidate_completion_rate, 1.0)

    def test_dynamic_value_strings_are_escaped_with_the_standard_library(self) -> None:
        with patch(
            "src.engines.backtesting.reporting.escape",
            side_effect=lambda value, quote: f"escaped:{value}",
        ) as escape:
            rendered = HtmlOptimizationRunSummaryReportRenderer().render(_report(()))

        self.assertEqual(escape.call_count, 10)
        self.assertIn("<td>escaped:0</td>", rendered.payload)
        self.assertIn("<td>escaped:0.0</td>", rendered.payload)

    def test_invalid_inputs_and_public_export(self) -> None:
        renderer = HtmlOptimizationRunSummaryReportRenderer()
        report = _report(())

        for value in (
            None,
            report.analysis,
            report.analysis.summaries,
            report.analysis.aggregate,
            report.analysis.rates,
            {},
            "report",
        ):
            with self.subTest(value=value), self.assertRaisesRegex(TypeError, "report"):
                renderer.render(value)  # type: ignore[arg-type]

        from src.engines.backtesting import (
            HtmlOptimizationRunSummaryReportRenderer as PackageRenderer,
        )

        self.assertIs(PackageRenderer, HtmlOptimizationRunSummaryReportRenderer)
        self.assertEqual(report.analysis.aggregate.run_count, 0)


_EXHAUSTED = OptimizationTerminationReason.SEARCH_SPACE_EXHAUSTED
_BUDGET = OptimizationTerminationReason.EVALUATION_BUDGET_REACHED
_METRICS = (
    "Run Count",
    "Evaluated Candidate Count",
    "Total Eligible Candidate Count",
    "Recorded Rejection Count",
    "Search Space Exhausted Count",
    "Evaluation Budget Reached Count",
    "Candidate Completion Rate",
    "Recorded Rejection Rate",
    "Search Space Exhausted Rate",
    "Evaluation Budget Reached Rate",
)


def _expected_lines(*values: str) -> list[str]:
    """Return the fixed fragment structure with ordered supplied values."""
    lines = [
        "<section>",
        "<h1>Optimization Run Summary</h1>",
        "<table>",
        "<thead>",
        "<tr>",
        "<th>Metric</th>",
        "<th>Value</th>",
        "</tr>",
        "</thead>",
        "<tbody>",
    ]
    for metric, value in zip(_METRICS, values, strict=True):
        lines.extend(("<tr>", f"<td>{metric}</td>", f"<td>{value}</td>", "</tr>"))
    lines.extend(("</tbody>", "</table>", "</section>"))
    return lines


def _summary(
    name: str,
    evaluated_count: int,
    total_eligible_count: int,
    rejection_count: int,
    termination_reason: OptimizationTerminationReason,
) -> OptimizationRunSummary:
    """Return one immutable summary without optimization execution."""
    return OptimizationRunSummary(
        OptimizationStrategyMetadata(name),
        evaluated_count,
        total_eligible_count,
        0.0 if total_eligible_count == 0 else evaluated_count / total_eligible_count,
        termination_reason,
        rejection_count,
    )


def _report(
    summaries: tuple[OptimizationRunSummary, ...],
) -> OptimizationRunSummaryReport:
    """Build one immutable report from canonical existing analysis values."""
    return _report_from_summaries(OptimizationRunSummaries(summaries))


def _report_from_summaries(
    summaries: OptimizationRunSummaries,
) -> OptimizationRunSummaryReport:
    """Build one report without rendering or optimization execution."""
    return OptimizationRunSummaryReport.from_analysis(
        OptimizationRunSummaryAnalysis.from_summaries(summaries)
    )
