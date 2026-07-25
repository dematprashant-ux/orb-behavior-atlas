"""Performance Analytics structural contracts and pure construction functions."""

from src.engines.performance.builders import (
    build_performance_context,
    build_performance_metrics,
    build_performance_report,
    build_pnl_summary,
    build_trade_pnl,
)
from src.engines.performance.analyzer import BasicPerformanceEngine
from src.engines.performance.interfaces import (
    PerformanceAnalyzer,
    PerformanceEngine,
    PnLEngine,
)
from src.engines.performance.models import (
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

__all__ = [
    "PerformanceContext",
    "PerformanceAnalyzer",
    "PerformanceEngine",
    "PerformanceMetrics",
    "PerformanceReport",
    "PerformanceStatus",
    "PnLEngine",
    "PnLSummary",
    "BasicPerformanceEngine",
    "BasicPerformanceAnalyzer",
    "RealizedPnLEngine",
    "TradePnL",
    "TradeOutcome",
    "TradeOutcomeEngine",
    "TradeOutcomeType",
    "build_performance_context",
    "build_performance_metrics",
    "build_performance_report",
    "build_pnl_summary",
    "build_trade_pnl",
    "build_trade_outcome",
]
