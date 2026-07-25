"""Immutable portfolio lifecycle inputs for the portfolio state-transition engine."""

from dataclasses import dataclass
from datetime import datetime
from math import isfinite

from src.engines.data.models.types import Instrument
from src.engines.execution.models import ExecutionSide

__all__ = ["PortfolioCloseEvent", "PortfolioEvent", "PortfolioOpenEvent"]


@dataclass(frozen=True, slots=True)
class PortfolioOpenEvent:
    """Requests an active position using explicit portfolio lifecycle facts."""

    position_id: str
    instrument: Instrument
    side: ExecutionSide
    entry_price: float
    timestamp: datetime

    def __post_init__(self) -> None:
        """Require intrinsic opening facts without allocating or mutating cash."""
        _validate_position_id(self.position_id)
        if not isinstance(self.instrument, Instrument):
            raise TypeError("instrument must be an Instrument.")
        if not isinstance(self.side, ExecutionSide):
            raise TypeError("side must be an ExecutionSide.")
        _validate_positive_float(self.entry_price, "entry_price")
        _validate_aware_datetime(self.timestamp, "timestamp")


@dataclass(frozen=True, slots=True)
class PortfolioCloseEvent:
    """Requests closure of one active position at an explicit exit price."""

    position_id: str
    exit_price: float
    timestamp: datetime

    def __post_init__(self) -> None:
        """Require intrinsic closing facts without calculating profitability."""
        _validate_position_id(self.position_id)
        _validate_positive_float(self.exit_price, "exit_price")
        _validate_aware_datetime(self.timestamp, "timestamp")


PortfolioEvent = PortfolioOpenEvent | PortfolioCloseEvent


def _validate_position_id(value: str) -> None:
    """Require one explicit non-empty stable position identity."""
    if not isinstance(value, str):
        raise TypeError("position_id must be a str.")
    if not value:
        raise ValueError("position_id must not be empty.")


def _validate_aware_datetime(value: datetime, field_name: str) -> None:
    """Require an aware event timestamp without applying calendar semantics."""
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime.")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware.")


def _validate_positive_float(value: float, field_name: str) -> None:
    """Require a finite positive native float without accepting booleans."""
    if isinstance(value, bool) or not isinstance(value, float):
        raise TypeError(f"{field_name} must be a float.")
    if not isfinite(value):
        raise ValueError(f"{field_name} must be finite.")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive.")
