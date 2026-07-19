"""Pure Backtesting Engine protocol boundary without a backtest implementation."""

from typing import Protocol

from src.engines.backtesting.models import BacktestContext, BacktestRun

__all__ = ["BacktestEngine"]


class BacktestEngine(Protocol):
    """Defines the pure run contract for a future backtest implementation."""

    def run(self, context: BacktestContext) -> BacktestRun:
        """Return a structural run without implying replay or simulation behavior."""
