"""Contract tests for deterministic gross or net analytics composition."""

from dataclasses import FrozenInstanceError, is_dataclass
from unittest import TestCase

from src.engines.backtesting import FixedRateTransactionCostModel
from src.engines.execution import ExecutionSide, build_completed_trade
from src.engines.performance import (
    BacktestAnalyticsPipeline,
    BasicDrawdownAnalyzer,
    BasicPerformanceAnalyzer,
    BasicRiskMetricsAnalyzer,
    CumulativeEquityCurveBuilder,
    EquityCurveMode,
    PerformanceMetricMode,
    RealizedPnLEngine,
    StandardBacktestAnalyticsPipeline,
    build_backtest_report,
)

from tests.test_completed_trade_execution import _accepted_result


class BacktestAnalyticsPipelineTests(TestCase):
    """Verify injected collaborators preserve one canonical analytics mode."""

    def test_default_and_explicit_gross_modes_preserve_existing_analytics(self) -> None:
        """Build equal gross reports without changing existing formulas."""
        default_report = _pipeline().run(_trades())
        explicit_report = _pipeline(PerformanceMetricMode.GROSS).run(_trades())

        self.assertEqual(default_report, explicit_report)
        self.assertIs(default_report.mode, PerformanceMetricMode.GROSS)
        self.assertEqual(default_report.performance_metrics.net_profit, 5.0)
        self.assertEqual(default_report.equity_curve.final_equity, 5.0)

    def test_fixed_costs_are_retained_once_and_net_analytics_are_reduced(self) -> None:
        """Select existing gross or net PnL without a second cost subtraction."""
        gross_pnl = _RecordingPnLEngine(_fixed_cost_pnl_engine())
        net_pnl = _RecordingPnLEngine(_fixed_cost_pnl_engine())

        gross = _pipeline(pnl_engine=gross_pnl).run(_trades())
        net = _pipeline(PerformanceMetricMode.NET, net_pnl).run(_trades())

        self.assertEqual((gross_pnl.calls, net_pnl.calls), (1, 1))
        self.assertEqual(gross_pnl.summary.trade_pnls[0].transaction_cost, 21.0)
        self.assertEqual(gross.performance_metrics.net_profit, 5.0)
        self.assertEqual(net.performance_metrics.net_profit, -35.5)
        self.assertEqual((gross.equity_curve.final_equity, net.equity_curve.final_equity), (5.0, -35.5))
        self.assertIs(net.mode, PerformanceMetricMode.NET)

    def test_collaborators_run_once_in_stable_order(self) -> None:
        """Delegate each stage once before one report construction."""
        events: list[str] = []
        pipeline = _pipeline(events=events)

        report = pipeline.run(_trades())

        self.assertIs(report.mode, PerformanceMetricMode.GROSS)
        self.assertEqual(events, ["pnl", "performance", "equity", "drawdown", "risk", "report"])

    def test_failure_propagates_without_later_calls_or_partial_report(self) -> None:
        """Do not catch a PnL failure or proceed to report construction."""
        events: list[str] = []
        pipeline = _pipeline(pnl_engine=_FailingPnLEngine(events), events=events)

        with self.assertRaisesRegex(RuntimeError, "pnl failure"):
            pipeline.run(_trades())
        self.assertEqual(events, ["pnl"])

    def test_pipeline_is_immutable_and_rejects_intrinsic_misuse(self) -> None:
        """Require collaborators, a mode enum, and a completed-trade tuple."""
        pipeline = _pipeline()

        self.assertTrue(is_dataclass(pipeline))
        self.assertFalse(hasattr(pipeline, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            pipeline.mode = PerformanceMetricMode.NET
        with self.assertRaises(TypeError):
            _pipeline(mode="NET")
        with self.assertRaises(TypeError):
            StandardBacktestAnalyticsPipeline(
                pnl_engine=None,
                performance_analyzer=BasicPerformanceAnalyzer(),
                equity_curve_builder=CumulativeEquityCurveBuilder(),
                drawdown_analyzer=BasicDrawdownAnalyzer(),
                risk_metrics_analyzer=BasicRiskMetricsAnalyzer(),
            )
        with self.assertRaises(TypeError):
            pipeline.run([])

    def test_public_protocol_accepts_the_deterministic_pipeline(self) -> None:
        """Exercise the new public orchestration contract through a consumer."""
        report = _run(_pipeline(), _trades())

        self.assertIs(report.mode, PerformanceMetricMode.GROSS)


def _pipeline(
    mode: PerformanceMetricMode = PerformanceMetricMode.GROSS,
    pnl_engine=None,
    events: list[str] | None = None,
) -> StandardBacktestAnalyticsPipeline:
    """Build fully injected existing collaborators for the selected mode."""
    pnl = RealizedPnLEngine() if pnl_engine is None else pnl_engine
    recorded_pnl = (
        pnl
        if isinstance(pnl, _FailingPnLEngine)
        else _RecordingPnLEngine(pnl, events)
    )
    return StandardBacktestAnalyticsPipeline(
        pnl_engine=recorded_pnl if events is not None else pnl,
        performance_analyzer=_RecordingPerformanceAnalyzer(mode, events),
        equity_curve_builder=_RecordingEquityBuilder(mode, events),
        drawdown_analyzer=_RecordingDrawdownAnalyzer(events),
        risk_metrics_analyzer=_RecordingRiskAnalyzer(events),
        report_builder=_report_builder(events),
        mode=mode,
    )


def _fixed_cost_pnl_engine() -> RealizedPnLEngine:
    """Build the existing PnL engine with one injected fixed-rate cost model."""
    return RealizedPnLEngine(
        FixedRateTransactionCostModel(0.1, 0.0, 0.0, 0.0, 0.0)
    )


def _report_builder(events: list[str] | None):
    """Return a pure report-builder collaborator with optional call recording."""
    def build(*args):
        if events is not None:
            events.append("report")
        return build_backtest_report(*args)

    return build


def _run(pipeline: BacktestAnalyticsPipeline, trades):
    """Use the public protocol without accessing concrete pipeline internals."""
    return pipeline.run(trades)


class _RecordingPnLEngine:
    """Test-only wrapper around one existing PnL engine."""

    def __init__(self, engine, events: list[str] | None = None):
        self.engine = engine
        self.events = events
        self.calls = 0
        self.summary = None

    def calculate(self, trades):
        self.calls += 1
        if self.events is not None:
            self.events.append("pnl")
        self.summary = self.engine.calculate(trades)
        return self.summary


class _RecordingPerformanceAnalyzer:
    def __init__(self, mode, events):
        self.engine = BasicPerformanceAnalyzer(mode)
        self.events = events

    def analyze(self, summary):
        if self.events is not None:
            self.events.append("performance")
        return self.engine.analyze(summary)


class _RecordingEquityBuilder:
    def __init__(self, mode, events):
        equity_mode = (
            EquityCurveMode.GROSS
            if mode is PerformanceMetricMode.GROSS
            else EquityCurveMode.NET
        )
        self.engine = CumulativeEquityCurveBuilder(equity_mode)
        self.events = events

    def build(self, summary):
        if self.events is not None:
            self.events.append("equity")
        return self.engine.build(summary)


class _RecordingDrawdownAnalyzer:
    def __init__(self, events):
        self.engine = BasicDrawdownAnalyzer()
        self.events = events

    def analyze(self, curve):
        if self.events is not None:
            self.events.append("drawdown")
        return self.engine.analyze(curve)


class _RecordingRiskAnalyzer:
    def __init__(self, events):
        self.engine = BasicRiskMetricsAnalyzer()
        self.events = events

    def analyze(self, performance, drawdown):
        if self.events is not None:
            self.events.append("risk")
        return self.engine.analyze(performance, drawdown)


class _FailingPnLEngine:
    def __init__(self, events):
        self.events = events

    def calculate(self, trades):
        self.events.append("pnl")
        raise RuntimeError("pnl failure")


def _trades():
    """Build immutable completed trades with gross PnL values of 10 and -5."""
    return (
        build_completed_trade(_accepted_result(), ExecutionSide.LONG, 1, 100.0, 110.0),
        build_completed_trade(_accepted_result(), ExecutionSide.LONG, 1, 100.0, 95.0),
    )
