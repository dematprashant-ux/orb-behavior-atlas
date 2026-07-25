"""Contract tests for immutable optimization summary report-domain models."""

from dataclasses import FrozenInstanceError
from unittest import TestCase
from unittest.mock import patch

from src.engines.backtesting import (
    OptimizationRunSummaries,
    OptimizationRunSummary,
    OptimizationRunSummaryAggregate,
    OptimizationRunSummaryAnalysis,
    OptimizationRunSummaryCatalog,
    OptimizationRunSummaryComparison,
    OptimizationRunSummaryDelta,
    OptimizationRunSummaryRates,
    OptimizationRunSummaryReport,
    OptimizationStrategyMetadata,
    OptimizationTerminationReason,
)


class OptimizationRunSummaryReportTests(TestCase):
    """Verify reports retain one existing canonical analysis without behavior."""

    def test_report_is_immutable_deterministic_and_retains_analysis_identity(
        self,
    ) -> None:
        analysis = _analysis((_summary("grid"), _summary("random")))

        report = OptimizationRunSummaryReport.from_analysis(analysis)

        self.assertIs(report.analysis, analysis)
        self.assertEqual(report, OptimizationRunSummaryReport.from_analysis(analysis))
        self.assertEqual(
            repr(report),
            repr(OptimizationRunSummaryReport.from_analysis(analysis)),
        )
        with self.assertRaises(FrozenInstanceError):
            report.analysis = analysis  # type: ignore[misc]

    def test_factory_does_not_reconstruct_or_traverse_analysis_components(self) -> None:
        summaries = OptimizationRunSummaries((_summary("grid"), _summary("grid")))
        analysis = OptimizationRunSummaryAnalysis.from_summaries(summaries)

        with patch.object(
            OptimizationRunSummaries,
            "__iter__",
            side_effect=AssertionError("summaries must not be traversed"),
        ), patch.object(
            OptimizationRunSummaryAggregate,
            "from_summaries",
            side_effect=AssertionError("aggregate must not be reconstructed"),
        ), patch.object(
            OptimizationRunSummaryRates,
            "from_aggregate",
            side_effect=AssertionError("rates must not be reconstructed"),
        ):
            report = OptimizationRunSummaryReport.from_analysis(analysis)

        self.assertIs(report.analysis, analysis)
        self.assertIs(report.analysis.summaries, summaries)
        self.assertEqual(
            tuple(report.analysis.summaries),
            (summaries[0], summaries[1]),
        )

    def test_empty_analysis_retains_existing_zero_components_by_identity(self) -> None:
        analysis = _analysis(())

        report = OptimizationRunSummaryReport.from_analysis(analysis)

        self.assertIs(report.analysis, analysis)
        self.assertEqual(
            report.analysis.aggregate,
            OptimizationRunSummaryAggregate(0, 0, 0, 0, 0, 0),
        )
        self.assertEqual(
            report.analysis.rates,
            OptimizationRunSummaryRates(0.0, 0.0, 0.0, 0.0),
        )

    def test_invalid_inputs_are_rejected_without_mutating_existing_artifacts(
        self,
    ) -> None:
        analysis = _analysis(())
        comparison = OptimizationRunSummaryComparison.between(analysis, analysis)
        catalog = OptimizationRunSummaryCatalog((comparison,))
        delta = OptimizationRunSummaryDelta.between(analysis, analysis)

        for value in (
            None,
            (),
            analysis.summaries,
            analysis.aggregate,
            analysis.rates,
            delta,
            comparison,
            catalog,
        ):
            with self.subTest(value=value), self.assertRaisesRegex(
                TypeError,
                "analysis",
            ):
                OptimizationRunSummaryReport.from_analysis(
                    value
                )  # type: ignore[arg-type]

        self.assertEqual(analysis.aggregate.run_count, 0)
        self.assertEqual(analysis.rates.candidate_completion_rate, 0.0)

    def test_report_exposes_no_rendering_or_persistence_api_and_is_exported(
        self,
    ) -> None:
        report = OptimizationRunSummaryReport.from_analysis(_analysis(()))

        for name in (
            "render",
            "format",
            "to_text",
            "to_markdown",
            "to_html",
            "to_table",
            "write",
            "save",
            "print",
            "export",
            "serialize",
        ):
            self.assertFalse(hasattr(report, name))

        from src.engines.backtesting import (
            OptimizationRunSummaryReport as PackageReport,
        )

        self.assertIs(PackageReport, OptimizationRunSummaryReport)


_EXHAUSTED = OptimizationTerminationReason.SEARCH_SPACE_EXHAUSTED


def _summary(name: str) -> OptimizationRunSummary:
    """Return one existing immutable summary without optimization execution."""
    return OptimizationRunSummary(
        OptimizationStrategyMetadata(name),
        1,
        1,
        1.0,
        _EXHAUSTED,
        0,
    )


def _analysis(
    summaries: tuple[OptimizationRunSummary, ...],
) -> OptimizationRunSummaryAnalysis:
    """Build one canonical analysis from existing summary objects."""
    return OptimizationRunSummaryAnalysis.from_summaries(
        OptimizationRunSummaries(summaries)
    )
