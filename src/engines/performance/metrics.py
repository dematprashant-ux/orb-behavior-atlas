"""Deterministic aggregate trading metrics over immutable realized PnL."""

from src.engines.performance.builders import build_performance_metrics
from src.engines.performance.models import PerformanceMetrics, PnLSummary

__all__ = ["BasicPerformanceAnalyzer"]


class BasicPerformanceAnalyzer:
    """Calculate deterministic aggregate metrics without portfolio analytics."""

    def analyze(self, summary: PnLSummary) -> PerformanceMetrics:
        """Return unrounded counts, rates, averages, and profit factor.

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
        for trade_pnl in summary.trade_pnls:
            realized_pnl = trade_pnl.realized_pnl
            if realized_pnl > 0:
                winning_trades += 1
                gross_profit += realized_pnl
            elif realized_pnl < 0:
                losing_trades += 1
                gross_loss -= realized_pnl
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
            average_trade_pnl = summary.total_realized_pnl / total_trades
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
            net_profit=summary.total_realized_pnl,
            win_rate=win_rate,
            loss_rate=loss_rate,
            flat_rate=flat_rate,
            average_trade_pnl=average_trade_pnl,
            average_winning_trade=average_winning_trade,
            average_losing_trade=average_losing_trade,
            profit_factor=profit_factor,
            expectancy=expectancy,
        )
