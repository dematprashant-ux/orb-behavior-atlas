"""Deterministic aggregate trading metrics over immutable realized PnL."""

from dataclasses import dataclass

from src.engines.performance.builders import build_performance_metrics
from src.engines.performance.models import (
    PerformanceMetrics,
    PerformanceMetricMode,
    PnLSummary,
    TradePnL,
)

__all__ = ["BasicPerformanceAnalyzer"]


@dataclass(frozen=True, slots=True)
class BasicPerformanceAnalyzer:
    """Calculate deterministic gross or net metrics without portfolio analytics."""

    mode: PerformanceMetricMode = PerformanceMetricMode.GROSS

    def __post_init__(self) -> None:
        """Require a supported selected-PnL mode without inspecting summaries."""
        if not isinstance(self.mode, PerformanceMetricMode):
            raise TypeError("mode must be a PerformanceMetricMode.")

    def analyze(self, summary: PnLSummary) -> PerformanceMetrics:
        """Return unrounded metrics using the configured gross or net PnL facts.

        Args:
            summary: Existing immutable realized-PnL items and total.

        Returns:
            Immutable metrics using only the supplied PnL values.

        Raises:
            TypeError: If ``summary`` is not a ``PnLSummary``.
        """
        if not isinstance(summary, PnLSummary):
            raise TypeError("summary must be a PnLSummary.")

        winning_trades = 0
        losing_trades = 0
        flat_trades = 0
        gross_profit = 0.0
        gross_loss = 0.0
        selected_total = 0.0
        for trade_pnl in summary.trade_pnls:
            selected_pnl = _pnl_value_for_mode(trade_pnl, self.mode)
            selected_total += selected_pnl
            if selected_pnl > 0:
                winning_trades += 1
                gross_profit += selected_pnl
            elif selected_pnl < 0:
                losing_trades += 1
                gross_loss -= selected_pnl
            else:
                flat_trades += 1

        total_trades = len(summary.trade_pnls)
        if total_trades == 0:
            win_rate = 0.0
            loss_rate = 0.0
            flat_rate = 0.0
            average_trade_pnl = 0.0
            expectancy = 0.0
        else:
            win_rate = winning_trades / total_trades
            loss_rate = losing_trades / total_trades
            flat_rate = flat_trades / total_trades
            average_trade_pnl = selected_total / total_trades
            expectancy = average_trade_pnl

        average_winning_trade = (
            gross_profit / winning_trades if winning_trades else 0.0
        )
        average_losing_trade = -gross_loss / losing_trades if losing_trades else 0.0
        profit_factor = gross_profit / gross_loss if gross_loss else None
        return build_performance_metrics(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            flat_trades=flat_trades,
            gross_profit=gross_profit,
            gross_loss=gross_loss,
            net_profit=selected_total,
            win_rate=win_rate,
            loss_rate=loss_rate,
            flat_rate=flat_rate,
            average_trade_pnl=average_trade_pnl,
            average_winning_trade=average_winning_trade,
            average_losing_trade=average_losing_trade,
            profit_factor=profit_factor,
            expectancy=expectancy,
            mode=self.mode,
        )


def _pnl_value_for_mode(
    trade_pnl: TradePnL,
    mode: PerformanceMetricMode,
) -> float:
    """Select one existing PnL fact without recalculating any trade value."""
    if mode is PerformanceMetricMode.GROSS:
        return trade_pnl.gross_pnl
    return trade_pnl.net_pnl
