"""Pure cumulative realized-equity construction over immutable PnL summaries."""

from dataclasses import dataclass

from src.engines.performance.builders import build_equity_curve, build_equity_point
from src.engines.performance.models import (
    EquityCurve,
    EquityCurveMode,
    EquityPoint,
    PnLSummary,
)

__all__ = ["CumulativeEquityCurveBuilder"]


@dataclass(frozen=True, slots=True)
class CumulativeEquityCurveBuilder:
    """Build an ordered cumulative gross or net equity series from one summary."""

    mode: EquityCurveMode = EquityCurveMode.GROSS

    def __post_init__(self) -> None:
        """Require an explicit supported mode without inspecting PnL inputs."""
        if not isinstance(self.mode, EquityCurveMode):
            raise TypeError("mode must be an EquityCurveMode.")

    def build(self, summary: PnLSummary) -> EquityCurve:
        """Accumulate selected existing PnL values from zero starting equity.

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
            running_total += _pnl_value_for_mode(trade_pnl, self.mode)
            equity_points.append(build_equity_point(trade_pnl, running_total))
        return build_equity_curve(tuple(equity_points), mode=self.mode)


def _pnl_value_for_mode(
    trade_pnl: "TradePnL",
    mode: EquityCurveMode,
) -> float:
    """Select an existing gross or net fact without recalculating trade PnL."""
    if mode is EquityCurveMode.GROSS:
        return trade_pnl.gross_pnl
    return trade_pnl.net_pnl
