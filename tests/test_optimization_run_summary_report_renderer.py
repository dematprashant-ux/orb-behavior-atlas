"""Contract tests for the optimization summary report renderer protocol."""

from inspect import signature
from typing import Protocol, get_type_hints
from unittest import TestCase

from src.engines.backtesting import (
    OptimizationRunSummaryAnalysis,
    OptimizationRunSummaryReport,
    OptimizationRunSummaryReportRenderer,
    OptimizationRunSummaries,
)


class OptimizationRunSummaryReportRendererTests(TestCase):
    """Verify only the stateless renderer boundary exists in production code."""

    def test_renderer_is_a_generic_protocol_with_one_render_operation(self) -> None:
        self.assertTrue(issubclass(OptimizationRunSummaryReportRenderer, Protocol))
        self.assertTrue(OptimizationRunSummaryReportRenderer._is_protocol)
        self.assertEqual(
            {
                name
                for name in OptimizationRunSummaryReportRenderer.__dict__
                if not name.startswith("_")
            },
            {"render"},
        )

    def test_render_contract_accepts_one_report_and_leaves_output_generic(self) -> None:
        parameters = tuple(
            signature(OptimizationRunSummaryReportRenderer.render).parameters
        )
        hints = get_type_hints(OptimizationRunSummaryReportRenderer.render)

        self.assertEqual(parameters, ("self", "report"))
        self.assertIs(hints["report"], OptimizationRunSummaryReport)
        self.assertIn("_RenderedOptimizationRunSummaryReport", str(hints["return"]))

    def test_protocol_has_no_rendering_implementation_or_stateful_constructor(
        self,
    ) -> None:
        report = OptimizationRunSummaryReport.from_analysis(
            OptimizationRunSummaryAnalysis.from_summaries(
                OptimizationRunSummaries(())
            )
        )

        self.assertEqual(OptimizationRunSummaryReportRenderer.__slots__, ())
        self.assertFalse(hasattr(OptimizationRunSummaryReportRenderer, "write"))
        self.assertFalse(hasattr(OptimizationRunSummaryReportRenderer, "save"))
        self.assertFalse(hasattr(OptimizationRunSummaryReportRenderer, "export"))
        self.assertIs(report.analysis.summaries.summaries, ())

    def test_public_export_is_intentional(self) -> None:
        from src.engines.backtesting import (
            OptimizationRunSummaryReportRenderer as PackageRenderer,
        )
        from src.engines.backtesting.reporting import (
            OptimizationRunSummaryReportRenderer as ModuleRenderer,
        )

        self.assertIs(PackageRenderer, OptimizationRunSummaryReportRenderer)
        self.assertIs(ModuleRenderer, OptimizationRunSummaryReportRenderer)
