"""Contract tests for immutable generic optimization summary renderer output."""

from dataclasses import FrozenInstanceError
from unittest import TestCase

from src.engines.backtesting import (
    OptimizationRunSummaryRenderedReport,
    OptimizationRunSummaryReportRenderer,
)


class OptimizationRunSummaryRenderedReportTests(TestCase):
    """Verify renderer output is an immutable generic payload wrapper only."""

    def test_rendered_report_is_immutable_deterministic_and_retains_payload(
        self,
    ) -> None:
        payload = _Payload("rendered")

        first = OptimizationRunSummaryRenderedReport(payload)
        second = OptimizationRunSummaryRenderedReport(payload)

        self.assertIs(first.payload, payload)
        self.assertEqual(first, second)
        self.assertEqual(repr(first), repr(second))
        with self.assertRaises(FrozenInstanceError):
            first.payload = _Payload("other")  # type: ignore[misc]

    def test_generic_payload_is_not_normalized_or_given_a_concrete_format(self) -> None:
        payload = ("renderer", 1)

        rendered = OptimizationRunSummaryRenderedReport(payload)

        self.assertIs(rendered.payload, payload)
        self.assertNotIsInstance(rendered.payload, str)
        self.assertNotIsInstance(rendered.payload, bytes)

    def test_none_payload_is_rejected_and_protocol_remains_generic(self) -> None:
        with self.assertRaisesRegex(TypeError, "payload"):
            OptimizationRunSummaryRenderedReport(None)  # type: ignore[arg-type]

        self.assertTrue(OptimizationRunSummaryReportRenderer._is_protocol)

    def test_public_export_is_intentional(self) -> None:
        from src.engines.backtesting import (
            OptimizationRunSummaryRenderedReport as PackageRenderedReport,
        )
        from src.engines.backtesting.reporting import (
            OptimizationRunSummaryRenderedReport as ModuleRenderedReport,
        )

        self.assertIs(PackageRenderedReport, OptimizationRunSummaryRenderedReport)
        self.assertIs(ModuleRenderedReport, OptimizationRunSummaryRenderedReport)


class _Payload:
    """Minimal immutable-like test payload without selecting a renderer format."""

    def __init__(self, value: str) -> None:
        """Retain one deterministic test value."""
        self.value = value
