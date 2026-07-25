"""Pure Performance Analytics protocol boundary without an implementation."""

from collections.abc import Mapping
from typing import Protocol

from src.engines.execution.models import CompletedTrade
from src.engines.performance.models import (
    DrawdownSummary,
    BacktestReport,
    EquityCurve,
    PerformanceContext,
    PerformanceMetrics,
    PerformanceReport,
    PnLSummary,
    RiskAdjustedMetrics,
)

__all__ = [
    "EquityCurveBuilder",
    "DrawdownAnalyzer",
    "PerformanceAnalyzer",
    "PerformanceEngine",
    "PnLEngine",
    "RiskMetricsAnalyzer",
    "ReportSerializer",
]


class PerformanceEngine(Protocol):
    """Defines the pure contract for a future performance-analysis implementation."""

    def analyze(self, context: PerformanceContext) -> PerformanceReport:
        """Return a structural report without implying metric calculation."""


class PnLEngine(Protocol):
    """Defines the pure contract for deterministic realized-PnL calculation."""

    def calculate(self, trades: tuple[CompletedTrade, ...]) -> PnLSummary:
        """Return an immutable summary calculated only from explicit trade facts."""


class PerformanceAnalyzer(Protocol):
    """Defines pure aggregate analysis over an immutable realized-PnL summary."""

    def analyze(self, summary: PnLSummary) -> PerformanceMetrics:
        """Return deterministic non-portfolio performance metrics."""


class EquityCurveBuilder(Protocol):
    """Defines pure cumulative-equity construction from immutable realized PnL."""

    def build(self, summary: PnLSummary) -> EquityCurve:
        """Return an ordered immutable cumulative-realized-equity curve."""


class DrawdownAnalyzer(Protocol):
    """Defines pure absolute-drawdown analysis over immutable equity curves."""

    def analyze(self, curve: EquityCurve) -> DrawdownSummary:
        """Return ordered running peaks and absolute drawdowns."""


class RiskMetricsAnalyzer(Protocol):
    """Defines pure absolute-return-to-drawdown metric analysis."""

    def analyze(
        self,
        performance: PerformanceMetrics,
        drawdown: DrawdownSummary,
    ) -> RiskAdjustedMetrics:
        """Return zero-safe metrics from existing aggregate artifacts only."""


class ReportSerializer(Protocol):
    """Defines pure plain-data serialization of an immutable backtest report."""

    def serialize(self, report: BacktestReport) -> Mapping[str, object]:
        """Return deterministic in-memory data without rendering or I/O."""
