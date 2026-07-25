"""Protocol boundary for deterministic portfolio lifecycle transitions."""

from typing import Protocol

from src.engines.portfolio.events import PortfolioEvent
from src.engines.portfolio.models import PortfolioSnapshot

__all__ = ["PortfolioEngine"]


class PortfolioEngine(Protocol):
    """Defines immutable snapshot construction from ordered portfolio events."""

    def process(
        self,
        initial_snapshot: PortfolioSnapshot,
        events: tuple[PortfolioEvent, ...],
    ) -> tuple[PortfolioSnapshot, ...]:
        """Return the initial snapshot followed by one snapshot per event."""
