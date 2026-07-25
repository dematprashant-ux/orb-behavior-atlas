"""Pure cumulative realized-equity construction over immutable PnL summaries."""

from src.engines.performance.builders import build_equity_curve, build_equity_point
from src.engines.performance.models import EquityCurve, EquityPoint, PnLSummary

__all__ = ["CumulativeEquityCurveBuilder"]


class CumulativeEquityCurveBuilder:
    """Build an ordered cumulative realized-equity series from one PnL summary."""

    def build(self, summary: PnLSummary) -> EquityCurve:
        """Accumulate existing realized PnL values from a zero starting equity.

        Args:
            summary: Existing immutable PnL items in their canonical order.

        Returns:
            An immutable curve with one point per supplied trade-PnL item.

        Raises:
            TypeError: If ``summary`` is not a ``PnLSummary``.
        """
        if not isinstance(summary, PnLSummary):
            raise TypeError("summary must be a PnLSummary.")

        running_total = 0.0
        equity_points: list[EquityPoint] = []
        for trade_pnl in summary.trade_pnls:
            running_total += trade_pnl.realized_pnl
            equity_points.append(build_equity_point(trade_pnl, running_total))
        return build_equity_curve(tuple(equity_points))
