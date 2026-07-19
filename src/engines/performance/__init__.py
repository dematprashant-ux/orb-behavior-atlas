"""Performance Analytics structural contracts and pure construction functions."""

from src.engines.performance.builders import (
    build_performance_context,
    build_performance_report,
)
from src.engines.performance.analyzer import BasicPerformanceEngine
from src.engines.performance.interfaces import PerformanceEngine
from src.engines.performance.models import (
    PerformanceContext,
    PerformanceReport,
    PerformanceStatus,
    TradeOutcome,
    TradeOutcomeType,
)
from src.engines.performance.outcomes import TradeOutcomeEngine, build_trade_outcome

__all__ = [
    "PerformanceContext",
    "PerformanceEngine",
    "PerformanceReport",
    "PerformanceStatus",
    "BasicPerformanceEngine",
    "TradeOutcome",
    "TradeOutcomeEngine",
    "TradeOutcomeType",
    "build_performance_context",
    "build_performance_report",
    "build_trade_outcome",
]
