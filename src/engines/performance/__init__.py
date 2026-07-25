"""Performance Analytics structural contracts and pure construction functions."""

from src.engines.performance.builders import (
    build_performance_context,
    build_performance_report,
    build_pnl_summary,
    build_trade_pnl,
)
from src.engines.performance.analyzer import BasicPerformanceEngine
from src.engines.performance.interfaces import PerformanceEngine, PnLEngine
from src.engines.performance.models import (
    PerformanceContext,
    PerformanceReport,
    PerformanceStatus,
    PnLSummary,
    TradePnL,
    TradeOutcome,
    TradeOutcomeType,
)
from src.engines.performance.outcomes import TradeOutcomeEngine, build_trade_outcome
from src.engines.performance.pnl import RealizedPnLEngine

__all__ = [
    "PerformanceContext",
    "PerformanceEngine",
    "PerformanceReport",
    "PerformanceStatus",
    "PnLEngine",
    "PnLSummary",
    "BasicPerformanceEngine",
    "RealizedPnLEngine",
    "TradePnL",
    "TradeOutcome",
    "TradeOutcomeEngine",
    "TradeOutcomeType",
    "build_performance_context",
    "build_performance_report",
    "build_pnl_summary",
    "build_trade_pnl",
    "build_trade_outcome",
]
