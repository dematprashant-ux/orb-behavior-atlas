"""Pure portfolio-equity metrics and shared-mathematics drawdown analysis."""

from dataclasses import dataclass
from math import isfinite

from src.engines.performance._drawdown_values import calculate_absolute_drawdowns
from src.engines.portfolio.equity import PortfolioEquityCurve, PortfolioEquityPoint

__all__ = [
    "PortfolioDrawdownPoint",
    "PortfolioDrawdownSummary",
    "PortfolioPerformanceMetrics",
    "StandardPortfolioDrawdownAnalyzer",
    "StandardPortfolioPerformanceAnalyzer",
    "build_portfolio_drawdown_summary",
    "build_portfolio_performance_metrics",
]


@dataclass(frozen=True, slots=True)
class PortfolioPerformanceMetrics:
    """Records deterministic return facts derived only from portfolio equity."""

    initial_equity: float
    final_equity: float
    absolute_return: float
    total_return: float | None
    maximum_equity: float
    minimum_equity: float
    equity_point_count: int

    def __post_init__(self) -> None:
        """Require exact values consistent with the documented empty-safe formulas."""
        for value, name in (
            (self.initial_equity, "initial_equity"),
            (self.final_equity, "final_equity"),
            (self.absolute_return, "absolute_return"),
            (self.maximum_equity, "maximum_equity"),
            (self.minimum_equity, "minimum_equity"),
        ):
            _validate_finite_float(value, name)
        _validate_count(self.equity_point_count)
        if self.initial_equity < 0 or self.final_equity < 0:
            raise ValueError("initial_equity and final_equity must be non-negative.")
        if self.maximum_equity < 0 or self.minimum_equity < 0:
            raise ValueError("equity extrema must be non-negative.")
        if self.minimum_equity > self.maximum_equity:
            raise ValueError("minimum_equity must not exceed maximum_equity.")
        if self.absolute_return != self.final_equity - self.initial_equity:
            raise ValueError("absolute_return must equal final minus initial equity.")
        _validate_total_return(self)


@dataclass(frozen=True, slots=True)
class PortfolioDrawdownPoint:
    """Records shared absolute-drawdown facts for one portfolio equity point."""

    source_equity_point: PortfolioEquityPoint
    running_peak: float
    drawdown: float

    def __post_init__(self) -> None:
        """Require finite non-negative values consistent with source total equity."""
        if not isinstance(self.source_equity_point, PortfolioEquityPoint):
            raise TypeError("source_equity_point must be a PortfolioEquityPoint.")
        _validate_finite_float(self.running_peak, "running_peak")
        _validate_finite_float(self.drawdown, "drawdown")
        if self.running_peak < self.source_equity_point.total_equity:
            raise ValueError("running_peak must not be below total equity.")
        if self.drawdown < 0:
            raise ValueError("drawdown must be non-negative.")
        if self.drawdown != self.running_peak - self.source_equity_point.total_equity:
            raise ValueError("drawdown must equal running peak minus total equity.")


@dataclass(frozen=True, slots=True)
class PortfolioDrawdownSummary:
    """Records ordered portfolio drawdowns and their maximum absolute value."""

    drawdown_points: tuple[PortfolioDrawdownPoint, ...]
    maximum_drawdown: float

    def __post_init__(self) -> None:
        """Require points with a consistent non-negative maximum drawdown."""
        if not isinstance(self.drawdown_points, tuple):
            raise TypeError(
                "drawdown_points must be a tuple of PortfolioDrawdownPoint values."
            )
        if any(
            not isinstance(point, PortfolioDrawdownPoint)
            for point in self.drawdown_points
        ):
            raise TypeError(
                "drawdown_points must contain only PortfolioDrawdownPoint values."
            )
        _validate_finite_float(self.maximum_drawdown, "maximum_drawdown")
        if self.maximum_drawdown < 0:
            raise ValueError("maximum_drawdown must be non-negative.")
        if any(
            current.running_peak < previous.running_peak
            for previous, current in zip(
                self.drawdown_points,
                self.drawdown_points[1:],
            )
        ):
            raise ValueError("running_peak must not decrease.")
        expected = max((point.drawdown for point in self.drawdown_points), default=0.0)
        if self.maximum_drawdown != expected:
            raise ValueError("maximum_drawdown must match supplied drawdown points.")


@dataclass(frozen=True, slots=True)
class StandardPortfolioPerformanceAnalyzer:
    """Analyze portfolio equity only; no positions, valuation, or trade facts."""

    def analyze(self, curve: PortfolioEquityCurve) -> PortfolioPerformanceMetrics:
        """Return deterministic empty-safe metrics from one existing curve."""
        if not isinstance(curve, PortfolioEquityCurve):
            raise TypeError("curve must be a PortfolioEquityCurve.")
        values = tuple(point.total_equity for point in curve.equity_points)
        if not values:
            return build_portfolio_performance_metrics(0.0, 0.0, 0.0, None, 0.0, 0.0, 0)
        initial_equity = values[0]
        final_equity = curve.final_equity
        absolute_return = final_equity - initial_equity
        total_return = absolute_return / initial_equity if initial_equity else None
        return build_portfolio_performance_metrics(
            initial_equity,
            final_equity,
            absolute_return,
            total_return,
            max(values),
            min(values),
            len(values),
        )


@dataclass(frozen=True, slots=True)
class StandardPortfolioDrawdownAnalyzer:
    """Adapt shared absolute-drawdown mathematics to portfolio equity points."""

    def analyze(self, curve: PortfolioEquityCurve) -> PortfolioDrawdownSummary:
        """Return ordered drawdowns without recalculating portfolio valuation."""
        if not isinstance(curve, PortfolioEquityCurve):
            raise TypeError("curve must be a PortfolioEquityCurve.")
        values = calculate_absolute_drawdowns(
            tuple(point.total_equity for point in curve.equity_points)
        )
        points = tuple(
            PortfolioDrawdownPoint(point, running_peak, drawdown)
            for point, (running_peak, drawdown) in zip(
                curve.equity_points,
                values,
                strict=True,
            )
        )
        return build_portfolio_drawdown_summary(points)


def build_portfolio_performance_metrics(
    initial_equity: float,
    final_equity: float,
    absolute_return: float,
    total_return: float | None,
    maximum_equity: float,
    minimum_equity: float,
    equity_point_count: int,
) -> PortfolioPerformanceMetrics:
    """Build immutable portfolio metrics without adding analytical formulas."""
    return PortfolioPerformanceMetrics(
        initial_equity,
        final_equity,
        absolute_return,
        total_return,
        maximum_equity,
        minimum_equity,
        equity_point_count,
    )


def build_portfolio_drawdown_summary(
    drawdown_points: tuple[PortfolioDrawdownPoint, ...],
    maximum_drawdown: float | None = None,
) -> PortfolioDrawdownSummary:
    """Build immutable portfolio drawdown output from existing point facts."""
    if not isinstance(drawdown_points, tuple):
        raise TypeError(
            "drawdown_points must be a tuple of PortfolioDrawdownPoint values."
        )
    if maximum_drawdown is None:
        maximum_drawdown = max(
            (point.drawdown for point in drawdown_points),
            default=0.0,
        )
    return PortfolioDrawdownSummary(drawdown_points, maximum_drawdown)


def _validate_count(value: int) -> None:
    """Require a non-negative integer count without accepting booleans."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("equity_point_count must be an int.")
    if value < 0:
        raise ValueError("equity_point_count must be non-negative.")


def _validate_finite_float(value: float, field_name: str) -> None:
    """Require a finite native float without accepting booleans or integers."""
    if isinstance(value, bool) or not isinstance(value, float):
        raise TypeError(f"{field_name} must be a float.")
    if not isfinite(value):
        raise ValueError(f"{field_name} must be finite.")


def _validate_total_return(metrics: PortfolioPerformanceMetrics) -> None:
    """Require the documented zero-safe total-return formula exactly."""
    expected = (
        metrics.absolute_return / metrics.initial_equity
        if metrics.initial_equity
        else None
    )
    if metrics.total_return is not None:
        _validate_finite_float(metrics.total_return, "total_return")
    if metrics.total_return != expected:
        raise ValueError(
            "total_return must equal absolute_return divided by initial_equity."
        )
