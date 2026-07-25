"""Immutable portfolio reporting and deterministic plain-data serialization."""

from dataclasses import dataclass
from typing import Protocol

from src.engines.portfolio.analytics import (
    PortfolioDrawdownSummary,
    PortfolioPerformanceMetrics,
)
from src.engines.portfolio.equity import PortfolioEquityCurve

__all__ = [
    "DictionaryPortfolioReportSerializer",
    "PortfolioReport",
    "PortfolioReportBuilder",
    "build_portfolio_report",
]


@dataclass(frozen=True, slots=True)
class PortfolioReport:
    """Composes existing portfolio analytics without recalculating any facts."""

    performance_metrics: PortfolioPerformanceMetrics
    equity_curve: PortfolioEquityCurve
    drawdown_summary: PortfolioDrawdownSummary

    def __post_init__(self) -> None:
        """Require only the upstream immutable analytics artifact types."""
        if not isinstance(self.performance_metrics, PortfolioPerformanceMetrics):
            raise TypeError("performance_metrics must be PortfolioPerformanceMetrics.")
        if not isinstance(self.equity_curve, PortfolioEquityCurve):
            raise TypeError("equity_curve must be a PortfolioEquityCurve.")
        if not isinstance(self.drawdown_summary, PortfolioDrawdownSummary):
            raise TypeError("drawdown_summary must be a PortfolioDrawdownSummary.")


class PortfolioReportBuilder(Protocol):
    """Defines pure composition of completed portfolio analytics artifacts."""

    def __call__(
        self,
        performance_metrics: PortfolioPerformanceMetrics,
        equity_curve: PortfolioEquityCurve,
        drawdown_summary: PortfolioDrawdownSummary,
    ) -> PortfolioReport:
        """Return one immutable report without rendering, I/O, or analytics."""


def build_portfolio_report(
    performance_metrics: PortfolioPerformanceMetrics,
    equity_curve: PortfolioEquityCurve,
    drawdown_summary: PortfolioDrawdownSummary,
) -> PortfolioReport:
    """Build an immutable portfolio report retaining upstream references."""
    return PortfolioReport(performance_metrics, equity_curve, drawdown_summary)


@dataclass(frozen=True, slots=True)
class DictionaryPortfolioReportSerializer:
    """Serialize a portfolio report to deterministic JSON-safe plain data."""

    def serialize(self, report: PortfolioReport) -> dict[str, object]:
        """Return ordered plain data without rendering or recalculating reports."""
        if not isinstance(report, PortfolioReport):
            raise TypeError("report must be a PortfolioReport.")
        metrics = report.performance_metrics
        curve = report.equity_curve
        drawdown = report.drawdown_summary
        return {
            "report_type": "portfolio",
            "performance_metrics": {
                "initial_equity": metrics.initial_equity,
                "final_equity": metrics.final_equity,
                "absolute_return": metrics.absolute_return,
                "total_return": metrics.total_return,
                "maximum_equity": metrics.maximum_equity,
                "minimum_equity": metrics.minimum_equity,
                "equity_point_count": metrics.equity_point_count,
            },
            "equity_curve": {
                "points": [
                    {
                        "timestamp": point.timestamp.isoformat(),
                        "cash": point.cash,
                        "position_value": point.position_value,
                        "total_equity": point.total_equity,
                    }
                    for point in curve.equity_points
                ],
                "final_equity": curve.final_equity,
            },
            "drawdown_summary": {
                "points": [
                    {
                        "timestamp": point.source_equity_point.timestamp.isoformat(),
                        "running_peak": point.running_peak,
                        "drawdown": point.drawdown,
                    }
                    for point in drawdown.drawdown_points
                ],
                "maximum_drawdown": drawdown.maximum_drawdown,
            },
        }
