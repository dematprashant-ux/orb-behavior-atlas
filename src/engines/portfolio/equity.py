"""Pure portfolio equity construction through an explicit valuation boundary."""

from dataclasses import dataclass, field
from datetime import datetime
from math import isfinite

from src.engines.portfolio.models import PortfolioSnapshot

__all__ = [
    "CostBasisPortfolioValuation",
    "PortfolioEquityCurve",
    "PortfolioEquityPoint",
    "StandardPortfolioEquityCurveBuilder",
    "build_portfolio_equity_curve",
    "build_portfolio_equity_point",
]


@dataclass(frozen=True, slots=True)
class PortfolioEquityPoint:
    """Records one explicit portfolio snapshot valuation at its timestamp."""

    timestamp: datetime
    cash: float
    position_value: float
    total_equity: float

    def __post_init__(self) -> None:
        """Require finite non-negative values with an exact total-equity identity."""
        _validate_aware_datetime(self.timestamp, "timestamp")
        _validate_non_negative_float(self.cash, "cash")
        _validate_non_negative_float(self.position_value, "position_value")
        _validate_non_negative_float(self.total_equity, "total_equity")
        if self.total_equity != self.cash + self.position_value:
            raise ValueError("total_equity must equal cash plus position_value.")


@dataclass(frozen=True, slots=True)
class PortfolioEquityCurve:
    """Records an ordered immutable portfolio equity series and final equity."""

    equity_points: tuple[PortfolioEquityPoint, ...]
    final_equity: float

    def __post_init__(self) -> None:
        """Require immutable valid points and a final value matching their order."""
        if not isinstance(self.equity_points, tuple):
            raise TypeError(
                "equity_points must be a tuple of PortfolioEquityPoint values."
            )
        if any(
            not isinstance(point, PortfolioEquityPoint)
            for point in self.equity_points
        ):
            raise TypeError(
                "equity_points must contain only PortfolioEquityPoint values."
            )
        _validate_non_negative_float(self.final_equity, "final_equity")
        expected_final_equity = (
            self.equity_points[-1].total_equity if self.equity_points else 0.0
        )
        if self.final_equity != expected_final_equity:
            raise ValueError("final_equity must match the last total_equity.")


@dataclass(frozen=True, slots=True)
class CostBasisPortfolioValuation:
    """Value active positions from their explicit entry costs only.

    This deterministic baseline does not imply a current market price or
    unrealized PnL. Alternate policies own their explicit valuation inputs.
    """

    def value(self, snapshot: PortfolioSnapshot) -> float:
        """Return active entry cost without fetching or inferring market values."""
        if not isinstance(snapshot, PortfolioSnapshot):
            raise TypeError("snapshot must be a PortfolioSnapshot.")
        return snapshot.invested_capital


@dataclass(frozen=True, slots=True)
class StandardPortfolioEquityCurveBuilder:
    """Build cash-plus-explicitly-valued-position equity in snapshot order."""

    valuation_policy: "PortfolioValuationPolicy" = field(
        default_factory=CostBasisPortfolioValuation
    )

    def __post_init__(self) -> None:
        """Require an injected policy object without invoking valuation."""
        if self.valuation_policy is None:
            raise TypeError("valuation_policy must not be None.")

    def build(self, snapshots: tuple[PortfolioSnapshot, ...]) -> PortfolioEquityCurve:
        """Return an immutable point for every supplied snapshot in its order."""
        if not isinstance(snapshots, tuple):
            raise TypeError("snapshots must be a tuple of PortfolioSnapshot values.")
        if any(not isinstance(snapshot, PortfolioSnapshot) for snapshot in snapshots):
            raise TypeError("snapshots must contain only PortfolioSnapshot values.")
        points = tuple(self._build_point(snapshot) for snapshot in snapshots)
        return build_portfolio_equity_curve(points)

    def _build_point(self, snapshot: PortfolioSnapshot) -> PortfolioEquityPoint:
        """Obtain explicit position value once and combine it with snapshot cash."""
        position_value = self.valuation_policy.value(snapshot)
        _validate_non_negative_float(position_value, "position_value")
        return build_portfolio_equity_point(
            snapshot.timestamp,
            snapshot.available_cash,
            position_value,
        )


def build_portfolio_equity_point(
    timestamp: datetime,
    cash: float,
    position_value: float,
    total_equity: float | None = None,
) -> PortfolioEquityPoint:
    """Build one equity point from explicit cash and position-valuation facts."""
    if total_equity is None:
        total_equity = cash + position_value
    return PortfolioEquityPoint(timestamp, cash, position_value, total_equity)


def build_portfolio_equity_curve(
    equity_points: tuple[PortfolioEquityPoint, ...],
    final_equity: float | None = None,
) -> PortfolioEquityCurve:
    """Build an ordered curve without sorting, pricing, or financial analysis."""
    if not isinstance(equity_points, tuple):
        raise TypeError("equity_points must be a tuple of PortfolioEquityPoint values.")
    if any(not isinstance(point, PortfolioEquityPoint) for point in equity_points):
        raise TypeError("equity_points must contain only PortfolioEquityPoint values.")
    if final_equity is None:
        final_equity = equity_points[-1].total_equity if equity_points else 0.0
    return PortfolioEquityCurve(equity_points, final_equity)


def _validate_aware_datetime(value: datetime, field_name: str) -> None:
    """Require an aware point timestamp without sorting or calendar inference."""
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime.")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware.")


def _validate_non_negative_float(value: float, field_name: str) -> None:
    """Require a finite non-negative native float without accepting booleans."""
    if isinstance(value, bool) or not isinstance(value, float):
        raise TypeError(f"{field_name} must be a float.")
    if not isfinite(value):
        raise ValueError(f"{field_name} must be finite.")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative.")
