"""Performance Analytics structural contracts and pure construction functions."""

from src.engines.performance.builders import (
    build_performance_context,
    build_performance_metrics,
    build_performance_report,
    build_equity_curve,
    build_equity_point,
    build_drawdown_point,
    build_drawdown_summary,
    build_risk_adjusted_metrics,
    build_backtest_report,
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
    RiskMetricsAnalyzer,
    ReportSerializer,
    JsonReportExporter,
    MarkdownReportRenderer,
    HtmlReportRenderer,
    ReportWriter,
)
from src.engines.performance.models import (
    BacktestReport,
    DrawdownPoint,
    DrawdownSummary,
    EquityCurve,
    EquityPoint,
    PerformanceContext,
    PerformanceMetrics,
    PerformanceReport,
    PerformanceStatus,
    PnLSummary,
    RiskAdjustedMetrics,
    TradePnL,
    TradeOutcome,
    TradeOutcomeType,
)
from src.engines.performance.outcomes import TradeOutcomeEngine, build_trade_outcome
from src.engines.performance.pnl import RealizedPnLEngine
from src.engines.performance.metrics import BasicPerformanceAnalyzer
from src.engines.performance.equity import CumulativeEquityCurveBuilder
from src.engines.performance.drawdown import BasicDrawdownAnalyzer
from src.engines.performance.risk import BasicRiskMetricsAnalyzer
from src.engines.performance.serialization import DictionaryReportSerializer
from src.engines.performance.json_export import StandardJsonReportExporter
from src.engines.performance.markdown import StandardMarkdownReportRenderer
from src.engines.performance.html import StandardHtmlReportRenderer
from src.engines.performance.writers import TextReportWriter

__all__ = [
    "BasicPerformanceAnalyzer",
    "BasicPerformanceEngine",
    "BasicDrawdownAnalyzer",
    "BasicRiskMetricsAnalyzer",
    "BacktestReport",
    "CumulativeEquityCurveBuilder",
    "DictionaryReportSerializer",
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
    "RiskAdjustedMetrics",
    "RiskMetricsAnalyzer",
    "ReportSerializer",
    "ReportWriter",
    "JsonReportExporter",
    "HtmlReportRenderer",
    "MarkdownReportRenderer",
    "RealizedPnLEngine",
    "StandardJsonReportExporter",
    "StandardMarkdownReportRenderer",
    "StandardHtmlReportRenderer",
    "TradePnL",
    "TextReportWriter",
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
    "build_risk_adjusted_metrics",
    "build_backtest_report",
    "build_pnl_summary",
    "build_trade_pnl",
    "build_trade_outcome",
]
