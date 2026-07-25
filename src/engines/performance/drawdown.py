"""Pure absolute-drawdown analysis over immutable gross or net equity curves."""

from src.engines.performance.builders import (
    build_drawdown_point,
    build_drawdown_summary,
)
from src.engines.performance.models import (
    DrawdownPoint,
    DrawdownSummary,
    EquityCurve,
)

__all__ = ["BasicDrawdownAnalyzer"]


class BasicDrawdownAnalyzer:
    """Calculate ordered absolute drawdowns from a zero starting-equity peak."""

    def analyze(self, curve: EquityCurve) -> DrawdownSummary:
        """Return running peaks and non-negative absolute drawdowns in curve order.

        Args:
            curve: Existing immutable cumulative gross or net equity curve.

        Returns:
            An immutable summary with one drawdown point per equity point.

        Raises:
            TypeError: If ``curve`` is not an ``EquityCurve``.
        """
        if not isinstance(curve, EquityCurve):
            raise TypeError("curve must be an EquityCurve.")

        running_peak = 0.0
        drawdown_points: list[DrawdownPoint] = []
        for equity_point in curve.equity_points:
            running_peak = max(running_peak, equity_point.cumulative_realized_pnl)
            drawdown = running_peak - equity_point.cumulative_realized_pnl
            drawdown_points.append(
                build_drawdown_point(equity_point, running_peak, drawdown)
            )
        return build_drawdown_summary(tuple(drawdown_points))
