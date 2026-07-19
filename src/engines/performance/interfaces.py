"""Pure Performance Analytics protocol boundary without an implementation."""

from typing import Protocol

from src.engines.performance.models import PerformanceContext, PerformanceReport

__all__ = ["PerformanceEngine"]


class PerformanceEngine(Protocol):
    """Defines the pure contract for a future performance-analysis implementation."""

    def analyze(self, context: PerformanceContext) -> PerformanceReport:
        """Return a structural report without implying metric calculation."""
