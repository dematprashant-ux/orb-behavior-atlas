"""Contract tests for deterministic plain-text optimization summary rendering."""

from unittest import TestCase
from unittest.mock import patch

from src.engines.backtesting import (
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


class PlainTextOptimizationRunSummaryReportRendererTests(TestCase):
    """Verify plain-text rendering reads only retained analytical scalar facts."""

    def test_renderer_is_stateless_and_satisfies_the_existing_protocol(self) -> None:
        renderer: OptimizationRunSummaryReportRenderer[str] = (
            PlainTextOptimizationRunSummaryReportRenderer()
        )

        self.assertEqual(renderer, PlainTextOptimizationRunSummaryReportRenderer())
        self.assertEqual(
            repr(renderer),
            repr(PlainTextOptimizationRunSummaryReportRenderer()),
        )
        self.assertEqual(PlainTextOptimizationRunSummaryReportRenderer.__slots__, ())

    def test_rendering_uses_fixed_heading_order_and_raw_retained_values(
        self,
    ) -> None:
        report = _report(
            (
                _summary("grid", 3, 3, 2, _EXHAUSTED),
                _summary("random", 1, 4, 1, _BUDGET),
            )
        )

        rendered = PlainTextOptimizationRunSummaryReportRenderer().render(report)

        self.assertIsInstance(rendered, OptimizationRunSummaryRenderedReport)
        self.assertIsInstance(rendered.payload, str)
        self.assertEqual(
            rendered.payload,
            "\n".join(
                (
                    "Optimization Run Summary",
                    "Run Count: 2",
                    "Evaluated Candidate Count: 4",
                    "Total Eligible Candidate Count: 7",
                    "Recorded Rejection Count: 3",
                    "Search Space Exhausted Count: 1",
                    "Evaluation Budget Reached Count: 1",
                    "Candidate Completion Rate: 0.5714285714285714",
                    "Recorded Rejection Rate: 0.42857142857142855",
                    "Search Space Exhausted Rate: 0.5",
                    "Evaluation Budget Reached Rate: 0.5",
                )
            ),
        )
        self.assertFalse(rendered.payload.startswith("\n"))
        self.assertFalse(rendered.payload.endswith("\n"))
        self.assertNotIn("\t", rendered.payload)
        self.assertNotIn("%", rendered.payload)
        self.assertTrue(
            all(line == line.rstrip() for line in rendered.payload.split("\n"))
        )

    def test_empty_report_renders_all_required_zero_values(self) -> None:
        rendered = PlainTextOptimizationRunSummaryReportRenderer().render(_report(()))

        self.assertEqual(
            rendered.payload.split("\n"),
            [
                "Optimization Run Summary",
                "Run Count: 0",
                "Evaluated Candidate Count: 0",
                "Total Eligible Candidate Count: 0",
                "Recorded Rejection Count: 0",
                "Search Space Exhausted Count: 0",
                "Evaluation Budget Reached Count: 0",
                "Candidate Completion Rate: 0.0",
                "Recorded Rejection Rate: 0.0",
                "Search Space Exhausted Rate: 0.0",
                "Evaluation Budget Reached Rate: 0.0",
            ],
        )

    def test_rendering_does_not_traverse_or_recalculate_analytical_components(
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
        ):
            first = PlainTextOptimizationRunSummaryReportRenderer().render(report)
            second = PlainTextOptimizationRunSummaryReportRenderer().render(report)

        self.assertEqual(first, second)
        self.assertEqual(report.analysis.aggregate.run_count, 1)
        self.assertEqual(report.analysis.rates.candidate_completion_rate, 1.0)

    def test_invalid_report_inputs_are_rejected_without_partial_output(self) -> None:
        renderer = PlainTextOptimizationRunSummaryReportRenderer()
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

        self.assertEqual(report.analysis.aggregate.run_count, 0)
        self.assertEqual(report.analysis.rates.candidate_completion_rate, 0.0)

    def test_public_export_is_intentional(self) -> None:
        from src.engines.backtesting import (
            PlainTextOptimizationRunSummaryReportRenderer as PackageRenderer,
        )
        from src.engines.backtesting.reporting import (
            PlainTextOptimizationRunSummaryReportRenderer as ModuleRenderer,
        )

        self.assertIs(PackageRenderer, PlainTextOptimizationRunSummaryReportRenderer)
        self.assertIs(ModuleRenderer, PlainTextOptimizationRunSummaryReportRenderer)


_EXHAUSTED = OptimizationTerminationReason.SEARCH_SPACE_EXHAUSTED
_BUDGET = OptimizationTerminationReason.EVALUATION_BUDGET_REACHED


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
    """Build one report without any rendering or optimization execution."""
    return OptimizationRunSummaryReport.from_analysis(
        OptimizationRunSummaryAnalysis.from_summaries(summaries)
    )
