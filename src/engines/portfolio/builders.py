"""Pure construction of immutable portfolio domain values."""

from datetime import datetime

from src.engines.data.models.types import Instrument
from src.engines.execution.models import ExecutionSide
from src.engines.portfolio.models import PortfolioPosition, PortfolioSnapshot

__all__ = ["build_portfolio_position", "build_portfolio_snapshot"]


def build_portfolio_position(
    position_id: str,
    instrument: Instrument,
    side: ExecutionSide,
    quantity: int,
    entry_price: float,
    entry_timestamp: datetime,
) -> PortfolioPosition:
    """Build one active position from explicit immutable entry facts."""
    return PortfolioPosition(
        position_id=position_id,
        instrument=instrument,
        side=side,
        quantity=quantity,
        entry_price=entry_price,
        entry_timestamp=entry_timestamp,
    )


def build_portfolio_snapshot(
    timestamp: datetime,
    available_cash: float,
    positions: tuple[PortfolioPosition, ...] = (),
) -> PortfolioSnapshot:
    """Build one cash-and-active-position snapshot without valuation."""
    return PortfolioSnapshot(
        timestamp=timestamp,
        available_cash=available_cash,
        positions=positions,
    )
