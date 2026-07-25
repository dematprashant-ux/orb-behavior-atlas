"""Immutable domain values for portfolio cash and active positions."""

from dataclasses import dataclass
from datetime import datetime
from math import isfinite

from src.engines.data.models.types import Instrument
from src.engines.execution.models import ExecutionSide

__all__ = ["PortfolioPosition", "PortfolioSnapshot"]


@dataclass(frozen=True, slots=True)
class PortfolioPosition:
    """Records one active holding using only explicit entry facts.

    A position's ``position_id`` is its stable portfolio identity. The model
    deliberately contains no valuation, exit, or profit-and-loss facts.
    """

    position_id: str
    instrument: Instrument
    side: ExecutionSide
    quantity: int
    entry_price: float
    entry_timestamp: datetime

    def __post_init__(self) -> None:
        """Require only intrinsic active-position facts."""
        if not isinstance(self.position_id, str):
            raise TypeError("position_id must be a str.")
        if not self.position_id:
            raise ValueError("position_id must not be empty.")
        if not isinstance(self.instrument, Instrument):
            raise TypeError("instrument must be an Instrument.")
        if not isinstance(self.side, ExecutionSide):
            raise TypeError("side must be an ExecutionSide.")
        _validate_positive_quantity(self.quantity)
        _validate_positive_float(self.entry_price, "entry_price")
        _validate_aware_datetime(self.entry_timestamp, "entry_timestamp")


@dataclass(frozen=True, slots=True)
class PortfolioSnapshot:
    """Records immutable available cash and ordered active positions in time.

    ``invested_capital`` is derived solely from explicit position entry facts;
    it is not a market valuation or an unrealized-profit calculation.
    """

    timestamp: datetime
    available_cash: float
    positions: tuple[PortfolioPosition, ...] = ()

    def __post_init__(self) -> None:
        """Require a non-negative cash balance and unique active identities."""
        _validate_aware_datetime(self.timestamp, "timestamp")
        _validate_non_negative_float(self.available_cash, "available_cash")
        if not isinstance(self.positions, tuple):
            raise TypeError("positions must be a tuple of PortfolioPosition values.")
        if any(
            not isinstance(position, PortfolioPosition)
            for position in self.positions
        ):
            raise TypeError("positions must contain only PortfolioPosition values.")
        position_ids = tuple(position.position_id for position in self.positions)
        if len(set(position_ids)) != len(position_ids):
            raise ValueError("positions must not contain duplicate position_id values.")

    @property
    def invested_capital(self) -> float:
        """Return explicit entry capital for active positions without valuation."""
        return sum(
            (position.entry_price * position.quantity for position in self.positions),
            start=0.0,
        )


def _validate_aware_datetime(value: datetime, field_name: str) -> None:
    """Require an aware ``datetime`` without applying calendar interpretation."""
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime.")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware.")


def _validate_positive_quantity(value: int) -> None:
    """Require a positive integer quantity without accepting booleans."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("quantity must be an int.")
    if value <= 0:
        raise ValueError("quantity must be positive.")


def _validate_positive_float(value: float, field_name: str) -> None:
    """Require a finite positive native float without accepting booleans."""
    _validate_finite_float(value, field_name)
    if value <= 0:
        raise ValueError(f"{field_name} must be positive.")


def _validate_non_negative_float(value: float, field_name: str) -> None:
    """Require a finite non-negative native float without accepting booleans."""
    _validate_finite_float(value, field_name)
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative.")


def _validate_finite_float(value: float, field_name: str) -> None:
    """Require a finite native float using the repository money convention."""
    if isinstance(value, bool) or not isinstance(value, float):
        raise TypeError(f"{field_name} must be a float.")
    if not isfinite(value):
        raise ValueError(f"{field_name} must be finite.")
