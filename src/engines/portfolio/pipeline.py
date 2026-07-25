"""Deterministic in-memory composition of the completed portfolio components."""

from dataclasses import dataclass

from src.engines.portfolio.engine import StandardPortfolioEngine
from src.engines.portfolio.events import PortfolioEvent
from src.engines.portfolio.equity import (
    PortfolioEquityCurve,
    StandardPortfolioEquityCurveBuilder,
)
from src.engines.portfolio.interfaces import (
    PortfolioDrawdownAnalyzer,
    PortfolioPerformanceAnalyzer,
)
from src.engines.portfolio.models import PortfolioSnapshot
from src.engines.portfolio.reporting import (
    PortfolioReport,
    PortfolioReportBuilder,
    build_portfolio_report,
)

__all__ = ["StandardPortfolioAnalyticsPipeline"]


@dataclass(frozen=True, slots=True)
class StandardPortfolioAnalyticsPipeline:
    """Coordinate injected portfolio collaborators without owning their formulas."""

    portfolio_engine: StandardPortfolioEngine
    equity_curve_builder: StandardPortfolioEquityCurveBuilder
    performance_analyzer: PortfolioPerformanceAnalyzer
    drawdown_analyzer: PortfolioDrawdownAnalyzer
    report_builder: PortfolioReportBuilder = build_portfolio_report

    def __post_init__(self) -> None:
        """Require injected collaborators without running transitions or analytics."""
        for collaborator, name in (
            (self.portfolio_engine, "portfolio_engine"),
            (self.equity_curve_builder, "equity_curve_builder"),
            (self.performance_analyzer, "performance_analyzer"),
            (self.drawdown_analyzer, "drawdown_analyzer"),
            (self.report_builder, "report_builder"),
        ):
            if collaborator is None:
                raise TypeError(f"{name} must not be None.")

    def run(
        self,
        initial_snapshot: PortfolioSnapshot,
        events: tuple[PortfolioEvent, ...],
    ) -> PortfolioReport:
        """Run one deterministic portfolio analysis through injected boundaries."""
        if not isinstance(initial_snapshot, PortfolioSnapshot):
            raise TypeError("initial_snapshot must be a PortfolioSnapshot.")
        if not isinstance(events, tuple):
            raise TypeError("events must be a tuple of PortfolioEvent values.")
        snapshots = self.portfolio_engine.process(initial_snapshot, events)
        curve = self.equity_curve_builder.build(snapshots)
        if not isinstance(curve, PortfolioEquityCurve):
            raise TypeError("equity_curve_builder must return a PortfolioEquityCurve.")
        performance = self.performance_analyzer.analyze(curve)
        drawdown = self.drawdown_analyzer.analyze(curve)
        return self.report_builder(performance, curve, drawdown)
