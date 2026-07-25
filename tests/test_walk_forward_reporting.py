"""Contract tests for walk-forward reporting, presentation, and orchestration."""

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta
from io import BytesIO
from unittest import TestCase

from pypdf import PdfReader

from src.engines.backtesting import (
    DateTimeRange,
    DictionaryWalkForwardReportSerializer,
    StandardWalkForwardAnalyticsPipeline,
    StandardWalkForwardHtmlRenderer,
    StandardWalkForwardMarkdownRenderer,
    StandardWalkForwardPdfRenderer,
    StandardWalkForwardReportBuilder,
    WalkForwardConfiguration,
    WalkForwardDatasetSplit,
    WalkForwardIterationResult,
    WalkForwardPlan,
    WalkForwardAnalyticsPipeline,
    WalkForwardReport,
    WalkForwardReportBuilder,
    WalkForwardRun,
    WalkForwardSelection,
    WalkForwardValidationResult,
    WalkForwardWindow,
)
from src.engines.backtesting.walk_forward.dataset import DatasetWindow
from src.engines.performance import StandardJsonReportExporter


class WalkForwardReportingTests(TestCase):
    """Verify pure report composition and deterministic in-memory presentation."""

    def test_builder_creates_immutable_empty_and_populated_structural_reports(self) -> None:
        builder: WalkForwardReportBuilder = StandardWalkForwardReportBuilder()
        empty = builder.build(WalkForwardRun(WalkForwardPlan()))
        populated_run = _run()
        populated = builder.build(populated_run)

        self.assertEqual(empty.summary.total_windows, 0)
        self.assertIsNone(empty.summary.earliest_training_start)
        self.assertIs(populated.run, populated_run)
        self.assertEqual(populated.summary.total_windows, 2)
        self.assertEqual(populated.summary.completed_iterations, 2)
        self.assertEqual(populated.summary.earliest_training_start, _time(0))
        self.assertEqual(populated.summary.latest_validation_end, _time(20))
        self.assertEqual(populated, builder.build(populated_run))
        with self.assertRaises(FrozenInstanceError):
            populated.run = empty.run  # type: ignore[misc]

    def test_serializer_and_existing_json_exporter_are_ordered_and_plain(self) -> None:
        report = StandardWalkForwardReportBuilder().build(_run())
        serializer = DictionaryWalkForwardReportSerializer()

        serialized = serializer.serialize(report)
        encoded = StandardJsonReportExporter().export(serialized)

        self.assertEqual(tuple(serialized), ("report_type", "summary", "iterations"))
        self.assertEqual([item["window_index"] for item in serialized["iterations"]], [0, 1])
        self.assertIn('"report_type":"walk_forward"', encoded)
        self.assertNotIn("WalkForward", encoded)
        self.assertEqual(serialized, serializer.serialize(report))

    def test_markdown_and_html_render_summary_and_ordered_iterations(self) -> None:
        serialized = DictionaryWalkForwardReportSerializer().serialize(
            StandardWalkForwardReportBuilder().build(_run())
        )
        serialized["iterations"][0]["selection_id"] = "<first & value>"

        markdown = StandardWalkForwardMarkdownRenderer().render(serialized)
        html = StandardWalkForwardHtmlRenderer().render(serialized)

        self.assertTrue(markdown.endswith("\n"))
        self.assertIn("# Walk-Forward Report", markdown)
        self.assertLess(markdown.index("| 0 |"), markdown.index("| 1 |"))
        self.assertIn("<first & value>", markdown)
        self.assertIn("<h1>Walk-Forward Report</h1>", html)
        self.assertIn("&lt;first &amp; value&gt;", html)
        self.assertNotIn("<first & value>", html)
        self.assertLess(html.index(">0</td>"), html.index(">1</td>"))

    def test_pdf_renderer_has_stable_visible_content_and_metadata(self) -> None:
        serialized = DictionaryWalkForwardReportSerializer().serialize(
            StandardWalkForwardReportBuilder().build(_run())
        )
        renderer = StandardWalkForwardPdfRenderer()
        first = PdfReader(BytesIO(renderer.render(serialized)))
        second = PdfReader(BytesIO(renderer.render(serialized)))
        text = "\n".join(page.extract_text() or "" for page in first.pages)

        self.assertIn("Walk-Forward Report", text)
        self.assertIn("Summary", text)
        self.assertIn("Iterations", text)
        self.assertLess(text.index("selection-0"), text.index("selection-1"))
        self.assertEqual(first.metadata, second.metadata)
        self.assertEqual(first.metadata.title, "Walk-Forward Report")
        self.assertNotIn("/CreationDate", first.metadata)
        self.assertNotIn("/ModDate", first.metadata)

    def test_pipeline_invokes_injected_collaborators_once_in_order(self) -> None:
        calls: list[str] = []
        plan = _run().plan
        run = _run()
        pipeline: WalkForwardAnalyticsPipeline = StandardWalkForwardAnalyticsPipeline(
            _Generator(plan, calls),
            _Runner(run, calls),
            _Builder(calls),
        )

        report = pipeline.run(_configuration(), ())

        self.assertEqual(calls, ["generate", "run", "build"])
        self.assertIs(report.run, run)
        self.assertEqual(report.summary.total_windows, 2)

    def test_pipeline_propagates_failures_without_partial_report(self) -> None:
        pipeline = StandardWalkForwardAnalyticsPipeline(
            _FailingGenerator(),
            _Runner(_run(), []),
            _Builder([]),
        )

        with self.assertRaisesRegex(RuntimeError, "generator failure"):
            pipeline.run(_configuration(), ())

    def test_public_exports_and_plain_data_validation_are_explicit(self) -> None:
        from src.engines.backtesting.walk_forward import WalkForwardReport as PackageReport

        self.assertIs(PackageReport, WalkForwardReport)
        with self.assertRaises(TypeError):
            DictionaryWalkForwardReportSerializer().serialize(object())
        with self.assertRaises(ValueError):
            StandardWalkForwardMarkdownRenderer().render({"report_type": "other"})


class _Generator:
    """Recording plan generator double."""

    def __init__(self, plan: WalkForwardPlan, calls: list[str]) -> None:
        self.plan = plan
        self.calls = calls

    def generate(self, configuration: WalkForwardConfiguration) -> WalkForwardPlan:
        del configuration
        self.calls.append("generate")
        return self.plan


class _Runner:
    """Recording runner double preserving the supplied generated plan contract."""

    def __init__(self, run: WalkForwardRun, calls: list[str]) -> None:
        self.run_value = run
        self.calls = calls

    def run(self, plan: WalkForwardPlan, observations: tuple[object, ...]) -> WalkForwardRun:
        del observations
        self.calls.append("run")
        if plan != self.run_value.plan:
            raise AssertionError("unexpected plan")
        return self.run_value


class _Builder:
    """Recording report builder double."""

    def __init__(self, calls: list[str]) -> None:
        self.calls = calls

    def build(self, run: WalkForwardRun) -> WalkForwardReport:
        self.calls.append("build")
        return StandardWalkForwardReportBuilder().build(run)


class _FailingGenerator:
    """Failure double proving the pipeline does not suppress collaborator errors."""

    def generate(self, configuration: WalkForwardConfiguration) -> WalkForwardPlan:
        del configuration
        raise RuntimeError("generator failure")


def _run() -> WalkForwardRun:
    """Create a deterministic two-iteration immutable run fixture."""
    windows = (_window(0, 0), _window(1, 10))
    plan = WalkForwardPlan(windows)
    iterations = tuple(_iteration(window) for window in windows)
    return WalkForwardRun(plan, iterations)


def _iteration(window: WalkForwardWindow) -> WalkForwardIterationResult:
    """Build a typed iteration retaining source-window ranges and selections."""
    split = WalkForwardDatasetSplit(
        window,
        DatasetWindow(window.training_range, ()),
        DatasetWindow(window.validation_range, ()),
    )
    selection = WalkForwardSelection(f"selection-{window.index}")
    return WalkForwardIterationResult(
        split,
        selection,
        WalkForwardValidationResult(selection, split.validation),
    )


def _configuration() -> WalkForwardConfiguration:
    """Create a valid configuration required only at the pipeline boundary."""
    return WalkForwardConfiguration(
        DateTimeRange(_time(0), _time(30)),
        timedelta(minutes=5),
        timedelta(minutes=5),
        timedelta(minutes=5),
    )


def _window(index: int, start: int) -> WalkForwardWindow:
    """Create one deterministic contiguous plan window."""
    training_start = _time(start)
    training_end = _time(start + 5)
    return WalkForwardWindow(
        index,
        DateTimeRange(training_start, training_end),
        DateTimeRange(training_end, _time(start + 10)),
    )


def _time(minutes: int) -> datetime:
    """Return an aware fixture boundary without session inference."""
    return datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=minutes)
