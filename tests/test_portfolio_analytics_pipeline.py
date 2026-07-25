"""Contract tests for deterministic portfolio analytics orchestration."""

from datetime import datetime, timedelta, timezone
from unittest import TestCase

from src.engines.data.models import Instrument
from src.engines.execution import ExecutionSide
from src.engines.portfolio import (
    FixedCapitalAllocationPolicy,
    PortfolioAnalyticsPipeline,
    PortfolioCloseEvent,
    PortfolioOpenEvent,
    StandardPortfolioAnalyticsPipeline,
    StandardPortfolioDrawdownAnalyzer,
    StandardPortfolioEngine,
    StandardPortfolioEquityCurveBuilder,
    StandardPortfolioPerformanceAnalyzer,
    build_portfolio_snapshot,
)


class PortfolioAnalyticsPipelineTests(TestCase):
    """Verify orchestration delegates each completed portfolio concern once."""

    def test_pipeline_composes_one_completed_position_in_stable_order(self) -> None:
        """Verify cash, valuation, return, and drawdown from one explicit sequence."""
        calls: list[str] = []
        pipeline = _pipeline(calls)
        initial = build_portfolio_snapshot(_timestamp(), 1_000.0)
        report = pipeline.run(
            initial,
            (
                _open("one", 100.0, 1),
                _close("one", 110.0, 2),
            ),
        )

        self.assertEqual(calls, ["engine", "equity", "performance", "drawdown", "report"])
        self.assertEqual(report.equity_curve.final_equity, 1_020.0)
        self.assertEqual(report.performance_metrics.total_return, 0.02)
        self.assertEqual(report.drawdown_summary.maximum_drawdown, 0.0)

    def test_pipeline_handles_empty_and_cash_only_portfolios_without_partial_results(self) -> None:
        """Compose the same boundaries for no events and no active positions."""
        calls: list[str] = []
        report = _pipeline(calls).run(
            build_portfolio_snapshot(_timestamp(), 500.0),
            (),
        )

        self.assertEqual(report.equity_curve.final_equity, 500.0)
        self.assertEqual(report.performance_metrics.total_return, 0.0)
        self.assertEqual(calls, ["engine", "equity", "performance", "drawdown", "report"])

    def test_pipeline_preserves_explicit_open_position_valuation(self) -> None:
        """Pass the exact engine snapshot collection to the injected valuation boundary."""
        calls: list[str] = []
        pipeline = StandardPortfolioAnalyticsPipeline(
            _RecordingEngine(calls),
            _RecordingEquityBuilder(calls, 350.0),
            _RecordingPerformance(calls),
            _RecordingDrawdown(calls),
            _recording_report_builder(calls),
        )
        report = pipeline.run(
            build_portfolio_snapshot(_timestamp(), 1_000.0),
            (_open("one", 100.0, 1),),
        )

        self.assertEqual(report.equity_curve.equity_points[-1].position_value, 350.0)
        self.assertEqual(calls, ["engine", "equity", "performance", "drawdown", "report"])

    def test_pipeline_propagates_each_collaborator_failure(self) -> None:
        """Do not retry, catch, or return a partial report after collaborator failure."""
        initial = build_portfolio_snapshot(_timestamp(), 1_000.0)
        for failing in ("engine", "equity", "performance", "drawdown", "report"):
            with self.subTest(failing=failing):
                with self.assertRaises(RuntimeError):
                    _failing_pipeline(failing).run(initial, ())

    def test_pipeline_is_protocol_compatible_and_rejects_boundary_misuse(self) -> None:
        """Expose a pure protocol-shaped boundary with explicit input failures."""
        pipeline: PortfolioAnalyticsPipeline = _pipeline([])
        with self.assertRaises(TypeError):
            pipeline.run(object(), ())
        with self.assertRaises(TypeError):
            pipeline.run(build_portfolio_snapshot(_timestamp(), 1_000.0), [])


def _pipeline(calls: list[str]) -> StandardPortfolioAnalyticsPipeline:
    """Build a fully recording concrete pipeline fixture."""
    return StandardPortfolioAnalyticsPipeline(
        _RecordingEngine(calls),
        _RecordingEquityBuilder(calls),
        _RecordingPerformance(calls),
        _RecordingDrawdown(calls),
        _recording_report_builder(calls),
    )


class _RecordingEngine:
    """Delegate real state transitions while recording one pipeline invocation."""

    def __init__(self, calls: list[str]) -> None:
        self._calls = calls
        self._engine = StandardPortfolioEngine(FixedCapitalAllocationPolicy(200.0))

    def process(self, initial_snapshot, events):
        self._calls.append("engine")
        return self._engine.process(initial_snapshot, events)


class _RecordingEquityBuilder:
    """Delegate explicit valuation while recording exact supplied snapshots."""

    def __init__(self, calls: list[str], position_value: float | None = None) -> None:
        self._calls = calls
        self._position_value = position_value

    def build(self, snapshots):
        self._calls.append("equity")
        if self._position_value is None:
            return StandardPortfolioEquityCurveBuilder().build(snapshots)
        return StandardPortfolioEquityCurveBuilder(_FixedValuation(self._position_value)).build(snapshots)


class _RecordingPerformance:
    """Delegate real metrics while recording its single curve input invocation."""

    def __init__(self, calls: list[str]) -> None:
        self._calls = calls

    def analyze(self, curve):
        self._calls.append("performance")
        return StandardPortfolioPerformanceAnalyzer().analyze(curve)


class _RecordingDrawdown:
    """Delegate shared drawdown while recording its single curve input invocation."""

    def __init__(self, calls: list[str]) -> None:
        self._calls = calls

    def analyze(self, curve):
        self._calls.append("drawdown")
        return StandardPortfolioDrawdownAnalyzer().analyze(curve)


def _recording_report_builder(calls: list[str]):
    """Return a builder that records composition and imports no rendering boundary."""
    def builder(performance, curve, drawdown):
        calls.append("report")
        from src.engines.portfolio import build_portfolio_report

        return build_portfolio_report(performance, curve, drawdown)

    return builder


def _failing_pipeline(failing: str) -> StandardPortfolioAnalyticsPipeline:
    """Build one pipeline whose selected collaborator raises deterministically."""
    return StandardPortfolioAnalyticsPipeline(
        _Failing("engine") if failing == "engine" else _RecordingEngine([]),
        _Failing("equity") if failing == "equity" else _RecordingEquityBuilder([]),
        _Failing("performance") if failing == "performance" else _RecordingPerformance([]),
        _Failing("drawdown") if failing == "drawdown" else _RecordingDrawdown([]),
        _Failing("report") if failing == "report" else _recording_report_builder([]),
    )


class _Failing:
    """Test-only collaborator that raises at any invoked pipeline method."""

    def __init__(self, name: str) -> None:
        self._name = name

    def process(self, *args):
        raise RuntimeError(self._name)

    def build(self, *args):
        raise RuntimeError(self._name)

    def analyze(self, *args):
        raise RuntimeError(self._name)

    def __call__(self, *args):
        raise RuntimeError(self._name)


class _FixedValuation:
    """Return explicit supplied open-position value without market-data access."""

    def __init__(self, value: float) -> None:
        self._value = value

    def value(self, snapshot):
        return self._value


def _open(position_id: str, price: float, minute: int) -> PortfolioOpenEvent:
    """Build one explicit deterministic portfolio open event."""
    return PortfolioOpenEvent(
        position_id,
        Instrument.BANKNIFTY,
        ExecutionSide.LONG,
        price,
        _timestamp(minute),
    )


def _close(position_id: str, price: float, minute: int) -> PortfolioCloseEvent:
    """Build one explicit deterministic portfolio close event."""
    return PortfolioCloseEvent(position_id, price, _timestamp(minute))


def _timestamp(minutes: int = 0) -> datetime:
    """Return an aware timestamp for deterministic pipeline fixtures."""
    return datetime(2026, 1, 1, 9, 15, tzinfo=timezone.utc) + timedelta(
        minutes=minutes
    )
