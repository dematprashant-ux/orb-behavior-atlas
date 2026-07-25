"""Performance Analytics structural contracts and pure construction functions."""

from src.engines.performance.builders import (
    build_performance_context,
    build_performance_metrics,
    build_performance_report,
    build_equity_curve,
    build_equity_point,
    build_pnl_summary,
    build_trade_pnl,
)
from src.engines.performance.analyzer import BasicPerformanceEngine
from src.engines.performance.interfaces import (
    EquityCurveBuilder,
    PerformanceAnalyzer,
    PerformanceEngine,
    PnLEngine,
)
from src.engines.performance.models import (
    EquityCurve,
    EquityPoint,
    PerformanceContext,
    PerformanceMetrics,
    PerformanceReport,
    PerformanceStatus,
    PnLSummary,
    TradePnL,
    TradeOutcome,
    TradeOutcomeType,
)
from src.engines.performance.outcomes import TradeOutcomeEngine, build_trade_outcome
from src.engines.performance.pnl import RealizedPnLEngine
from src.engines.performance.metrics import BasicPerformanceAnalyzer
from src.engines.performance.equity import CumulativeEquityCurveBuilder

__all__ = [
    "BasicPerformanceAnalyzer",
    "BasicPerformanceEngine",
    "CumulativeEquityCurveBuilder",
    "EquityCurve",
    "EquityCurveBuilder",
    "EquityPoint",
    "PerformanceContext",
    "PerformanceAnalyzer",
    "PerformanceEngine",
    "PerformanceMetrics",
    "PerformanceReport",
    "PerformanceStatus",
    "PnLEngine",
    "PnLSummary",
    "RealizedPnLEngine",
    "TradePnL",
    "TradeOutcome",
    "TradeOutcomeEngine",
    "TradeOutcomeType",
    "build_performance_context",
    "build_performance_metrics",
    "build_performance_report",
    "build_equity_curve",
    "build_equity_point",
    "build_pnl_summary",
    "build_trade_pnl",
    "build_trade_outcome",
]
