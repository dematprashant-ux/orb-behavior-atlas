"""Deterministic realized-PnL calculation from explicit completed trades."""

from dataclasses import dataclass, field

from src.engines.backtesting import TransactionCostModel, ZeroTransactionCostModel
from src.engines.execution.models import CompletedTrade
from src.engines.performance.builders import build_pnl_summary, build_trade_pnl
from src.engines.performance.models import PnLSummary, TradePnL, _calculate_realized_pnl

__all__ = ["RealizedPnLEngine"]


@dataclass(frozen=True, slots=True)
class RealizedPnLEngine:
    """Calculate gross and cost-adjusted net PnL from supplied trade facts.

    The injected model supplies costs. The default explicit zero-cost model
    preserves prior gross-PnL behavior, and summary aggregation remains gross
    until a later dedicated downstream integration milestone.
    """

    transaction_cost_model: TransactionCostModel = field(
        default_factory=ZeroTransactionCostModel
    )

    def __post_init__(self) -> None:
        """Require one injected transaction-cost collaborator without invoking it."""
        if self.transaction_cost_model is None:
            raise TypeError("transaction_cost_model must not be None.")

    def calculate(self, trades: tuple[CompletedTrade, ...]) -> PnLSummary:
        """Return ordered gross/net PnL and its gross aggregate total.

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
            self._calculate_trade_pnl(trade) for trade in trades
        )
        return build_pnl_summary(trade_pnls)

    def _calculate_trade_pnl(self, trade: CompletedTrade) -> TradePnL:
        """Build one gross/net PnL item from explicit trade and cost-model facts."""
        cost_breakdown = self.transaction_cost_model.calculate(
            entry_price=trade.entry_price,
            exit_price=trade.exit_price,
            quantity=trade.quantity,
        )
        return build_trade_pnl(
            trade,
            _calculate_realized_pnl(trade),
            transaction_cost=cost_breakdown.total_cost,
        )
