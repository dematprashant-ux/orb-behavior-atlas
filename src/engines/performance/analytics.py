"""Deterministic composition of existing gross or net analytics collaborators."""

from collections.abc import Callable
from dataclasses import dataclass

from src.engines.execution.models import CompletedTrade
from src.engines.performance.builders import build_backtest_report
from src.engines.performance.interfaces import (
    DrawdownAnalyzer,
    EquityCurveBuilder,
    PerformanceAnalyzer,
    PnLEngine,
    RiskMetricsAnalyzer,
)
from src.engines.performance.models import (
    BacktestReport,
    DrawdownSummary,
    EquityCurve,
    PerformanceMetrics,
    PerformanceMetricMode,
    RiskAdjustedMetrics,
)

__all__ = ["StandardBacktestAnalyticsPipeline"]

_ReportBuilder = Callable[
    [
        PerformanceMetrics,
        EquityCurve,
        DrawdownSummary,
        RiskAdjustedMetrics,
        PerformanceMetricMode,
    ],
    BacktestReport,
]


@dataclass(frozen=True, slots=True)
class StandardBacktestAnalyticsPipeline:
    """Coordinate injected collaborators into one complete immutable report."""

    pnl_engine: PnLEngine
    performance_analyzer: PerformanceAnalyzer
    equity_curve_builder: EquityCurveBuilder
    drawdown_analyzer: DrawdownAnalyzer
    risk_metrics_analyzer: RiskMetricsAnalyzer
    report_builder: _ReportBuilder = build_backtest_report
    mode: PerformanceMetricMode = PerformanceMetricMode.GROSS

    def __post_init__(self) -> None:
        """Require explicit injected collaborators and a canonical mode."""
        for collaborator, name in (
            (self.pnl_engine, "pnl_engine"),
            (self.performance_analyzer, "performance_analyzer"),
            (self.equity_curve_builder, "equity_curve_builder"),
            (self.drawdown_analyzer, "drawdown_analyzer"),
            (self.risk_metrics_analyzer, "risk_metrics_analyzer"),
            (self.report_builder, "report_builder"),
        ):
            if collaborator is None:
                raise TypeError(f"{name} must not be None.")
        if not isinstance(self.mode, PerformanceMetricMode):
            raise TypeError("mode must be a PerformanceMetricMode.")

    def run(self, trades: tuple[CompletedTrade, ...]) -> BacktestReport:
        """Delegate one completed-trade tuple through the existing analytics flow."""
        if not isinstance(trades, tuple):
            raise TypeError("trades must be a tuple of CompletedTrade values.")
        if any(not isinstance(trade, CompletedTrade) for trade in trades):
            raise TypeError("trades must contain only CompletedTrade values.")
        summary = self.pnl_engine.calculate(trades)
        performance = self.performance_analyzer.analyze(summary)
        if not isinstance(performance, PerformanceMetrics):
            raise TypeError("performance_analyzer must return PerformanceMetrics.")
        if performance.mode is not self.mode:
            raise ValueError("performance metrics mode must match pipeline mode.")
        curve = self.equity_curve_builder.build(summary)
        if not isinstance(curve, EquityCurve):
            raise TypeError("equity_curve_builder must return EquityCurve.")
        if curve.mode.value != self.mode.value:
            raise ValueError("equity curve mode must match pipeline mode.")
        drawdown = self.drawdown_analyzer.analyze(curve)
        risk = self.risk_metrics_analyzer.analyze(performance, drawdown)
        if not isinstance(risk, RiskAdjustedMetrics):
            raise TypeError("risk_metrics_analyzer must return RiskAdjustedMetrics.")
        if risk.mode.value != self.mode.value:
            raise ValueError("risk-adjusted metrics mode must match pipeline mode.")
        return self.report_builder(performance, curve, drawdown, risk, self.mode)
