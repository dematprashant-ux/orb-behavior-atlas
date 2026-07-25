"""Immutable Portfolio Engine domain contracts and pure builders."""

from src.engines.portfolio.builders import (
    build_portfolio_position,
    build_portfolio_snapshot,
)
from src.engines.portfolio.allocation import (
    AllocationDecision,
    AllocationRequest,
    CapitalAllocationPolicy,
    FixedCapitalAllocationPolicy,
    PercentageCapitalAllocationPolicy,
)
from src.engines.portfolio.models import PortfolioPosition, PortfolioSnapshot
from src.engines.portfolio.engine import StandardPortfolioEngine
from src.engines.portfolio.events import (
    PortfolioCloseEvent,
    PortfolioEvent,
    PortfolioOpenEvent,
)
from src.engines.portfolio.interfaces import PortfolioEngine
from src.engines.portfolio.interfaces import (
    PortfolioAnalyticsPipeline,
    PortfolioDrawdownAnalyzer,
    PortfolioEquityCurveBuilder,
    PortfolioPerformanceAnalyzer,
    PortfolioValuationPolicy,
)
from src.engines.portfolio.pipeline import StandardPortfolioAnalyticsPipeline
from src.engines.portfolio.equity import (
    CostBasisPortfolioValuation,
    PortfolioEquityCurve,
    PortfolioEquityPoint,
    StandardPortfolioEquityCurveBuilder,
    build_portfolio_equity_curve,
    build_portfolio_equity_point,
)
from src.engines.portfolio.analytics import (
    PortfolioDrawdownPoint,
    PortfolioDrawdownSummary,
    PortfolioPerformanceMetrics,
    StandardPortfolioDrawdownAnalyzer,
    StandardPortfolioPerformanceAnalyzer,
    build_portfolio_drawdown_summary,
    build_portfolio_performance_metrics,
)
from src.engines.portfolio.reporting import (
    DictionaryPortfolioReportSerializer,
    PortfolioReport,
    PortfolioReportBuilder,
    build_portfolio_report,
)

__all__ = [
    "AllocationDecision",
    "AllocationRequest",
    "CapitalAllocationPolicy",
    "CostBasisPortfolioValuation",
    "DictionaryPortfolioReportSerializer",
    "FixedCapitalAllocationPolicy",
    "PercentageCapitalAllocationPolicy",
    "PortfolioCloseEvent",
    "PortfolioAnalyticsPipeline",
    "PortfolioEngine",
    "PortfolioEquityCurve",
    "PortfolioEquityCurveBuilder",
    "PortfolioEquityPoint",
    "PortfolioDrawdownAnalyzer",
    "PortfolioDrawdownPoint",
    "PortfolioDrawdownSummary",
    "PortfolioEvent",
    "PortfolioOpenEvent",
    "PortfolioPosition",
    "PortfolioSnapshot",
    "PortfolioValuationPolicy",
    "PortfolioPerformanceAnalyzer",
    "PortfolioPerformanceMetrics",
    "PortfolioReport",
    "PortfolioReportBuilder",
    "StandardPortfolioDrawdownAnalyzer",
    "StandardPortfolioAnalyticsPipeline",
    "StandardPortfolioEquityCurveBuilder",
    "StandardPortfolioPerformanceAnalyzer",
    "StandardPortfolioEngine",
    "build_portfolio_position",
    "build_portfolio_snapshot",
    "build_portfolio_equity_curve",
    "build_portfolio_equity_point",
    "build_portfolio_drawdown_summary",
    "build_portfolio_performance_metrics",
    "build_portfolio_report",
]
