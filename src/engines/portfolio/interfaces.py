"""Protocol boundary for deterministic portfolio lifecycle transitions."""

from typing import Protocol

from src.engines.portfolio.events import PortfolioEvent
from src.engines.portfolio.models import PortfolioSnapshot

__all__ = [
    "PortfolioEngine",
    "PortfolioEquityCurveBuilder",
    "PortfolioPerformanceAnalyzer",
    "PortfolioDrawdownAnalyzer",
    "PortfolioAnalyticsPipeline",
    "PortfolioValuationPolicy",
]


class PortfolioEngine(Protocol):
    """Defines immutable snapshot construction from ordered portfolio events."""

    def process(
        self,
        initial_snapshot: PortfolioSnapshot,
        events: tuple[PortfolioEvent, ...],
    ) -> tuple[PortfolioSnapshot, ...]:
        """Return the initial snapshot followed by one snapshot per event."""


class PortfolioValuationPolicy(Protocol):
    """Defines explicit value determination for active portfolio positions."""

    def value(self, snapshot: PortfolioSnapshot) -> float:
        """Return finite non-negative value for a snapshot's active positions."""


class PortfolioEquityCurveBuilder(Protocol):
    """Defines pure portfolio-equity construction from ordered snapshots."""

    def build(self, snapshots: tuple[PortfolioSnapshot, ...]) -> "PortfolioEquityCurve":
        """Return ordered cash-plus-valued-position points without market access."""


class PortfolioPerformanceAnalyzer(Protocol):
    """Defines pure portfolio-equity metric analysis."""

    def analyze(self, curve: "PortfolioEquityCurve") -> "PortfolioPerformanceMetrics":
        """Return metrics computed only from the existing portfolio equity curve."""


class PortfolioDrawdownAnalyzer(Protocol):
    """Defines shared-mathematics absolute drawdown over portfolio equity."""

    def analyze(self, curve: "PortfolioEquityCurve") -> "PortfolioDrawdownSummary":
        """Return drawdown facts from the supplied portfolio equity curve."""


class PortfolioAnalyticsPipeline(Protocol):
    """Defines deterministic composition from initial state and portfolio events."""

    def run(
        self,
        initial_snapshot: PortfolioSnapshot,
        events: tuple[PortfolioEvent, ...],
    ) -> "PortfolioReport":
        """Return one complete report without rendering, I/O, or new formulas."""
