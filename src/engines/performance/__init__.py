"""Performance Analytics structural contracts and pure construction functions."""

from src.engines.performance.builders import (
    build_performance_context,
    build_performance_metrics,
    build_performance_report,
    build_equity_curve,
    build_equity_point,
    build_drawdown_point,
    build_drawdown_summary,
    build_pnl_summary,
    build_trade_pnl,
)
from src.engines.performance.analyzer import BasicPerformanceEngine
from src.engines.performance.interfaces import (
    DrawdownAnalyzer,
    EquityCurveBuilder,
    PerformanceAnalyzer,
    PerformanceEngine,
    PnLEngine,
)
from src.engines.performance.models import (
    DrawdownPoint,
    DrawdownSummary,
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
from src.engines.performance.drawdown import BasicDrawdownAnalyzer

__all__ = [
    "BasicPerformanceAnalyzer",
    "BasicPerformanceEngine",
    "BasicDrawdownAnalyzer",
    "CumulativeEquityCurveBuilder",
    "EquityCurve",
    "EquityCurveBuilder",
    "EquityPoint",
    "DrawdownAnalyzer",
    "DrawdownPoint",
    "DrawdownSummary",
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
    "build_drawdown_point",
    "build_drawdown_summary",
    "build_pnl_summary",
    "build_trade_pnl",
    "build_trade_outcome",
]
