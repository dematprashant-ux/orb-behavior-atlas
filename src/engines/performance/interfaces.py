"""Pure Performance Analytics protocol boundary without an implementation."""

from typing import Protocol

from src.engines.execution.models import CompletedTrade
from src.engines.performance.models import (
    PerformanceContext,
    PerformanceMetrics,
    PerformanceReport,
    PnLSummary,
)

__all__ = ["PerformanceAnalyzer", "PerformanceEngine", "PnLEngine"]


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
