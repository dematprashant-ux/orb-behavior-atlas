"""Deterministic realized-PnL calculation from explicit completed trades."""

from src.engines.execution.models import CompletedTrade
from src.engines.performance.builders import build_pnl_summary, build_trade_pnl
from src.engines.performance.models import PnLSummary, TradePnL, _calculate_realized_pnl

__all__ = ["RealizedPnLEngine"]


class RealizedPnLEngine:
    """Calculate realized PnL from supplied closed-trade facts only.

    The engine neither inspects candles nor infers prices, quantity, multipliers,
    lot size, fees, commissions, taxes, slippage, or any other trade fact.
    """

    def calculate(self, trades: tuple[CompletedTrade, ...]) -> PnLSummary:
        """Return ordered realized PnL and its native-float aggregate total.

        Args:
            trades: Existing immutable completed trades in caller-supplied order.

        Returns:
            An immutable summary with one PnL item for every supplied trade.

        Raises:
            TypeError: If ``trades`` is not a tuple of ``CompletedTrade`` values.
        """
        if not isinstance(trades, tuple):
            raise TypeError("trades must be a tuple of CompletedTrade values.")
        if any(not isinstance(trade, CompletedTrade) for trade in trades):
            raise TypeError("trades must contain only CompletedTrade values.")

        trade_pnls: tuple[TradePnL, ...] = tuple(
            build_trade_pnl(trade, _calculate_realized_pnl(trade))
            for trade in trades
        )
        return build_pnl_summary(trade_pnls)
