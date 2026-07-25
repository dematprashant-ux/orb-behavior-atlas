"""Contract tests for isolated gross-versus-net realized trade PnL."""

from dataclasses import FrozenInstanceError, is_dataclass
from unittest import TestCase

from src.engines.backtesting import FixedRateTransactionCostModel
from src.engines.execution import CompletedTrade, ExecutionSide, build_completed_trade
from src.engines.performance import RealizedPnLEngine, TradePnL, build_trade_pnl

from tests.test_completed_trade_execution import _accepted_result


class NetTradePnLTests(TestCase):
    """Verify injected costs affect only immutable per-trade net PnL facts."""

    def test_default_zero_cost_preserves_existing_gross_pnl_behavior(self) -> None:
        """Keep gross, compatibility, and net values identical by default."""
        trade_pnl = RealizedPnLEngine().calculate((_trade(),)).trade_pnls[0]

        self.assertEqual(trade_pnl.gross_pnl, 20.0)
        self.assertEqual(trade_pnl.realized_pnl, 20.0)
        self.assertEqual(trade_pnl.transaction_cost, 0.0)
        self.assertEqual(trade_pnl.net_pnl, 20.0)

    def test_fixed_rate_cost_propagates_without_changing_gross_summary(self) -> None:
        """Expose net PnL locally while the existing summary remains gross-only."""
        engine = RealizedPnLEngine(
            FixedRateTransactionCostModel(0.01, 0.0, 0.0, 0.0, 0.0)
        )

        summary = engine.calculate((_trade(),))
        trade_pnl = summary.trade_pnls[0]

        self.assertEqual(trade_pnl.gross_pnl, 20.0)
        self.assertEqual(trade_pnl.transaction_cost, 4.2)
        self.assertEqual(trade_pnl.net_pnl, 15.8)
        self.assertEqual(summary.total_realized_pnl, 20.0)

    def test_trade_pnl_validates_gross_cost_and_net_relationship(self) -> None:
        """Require exact immutable net PnL facts without changing gross meaning."""
        trade = _trade()
        trade_pnl = build_trade_pnl(trade, 20.0, transaction_cost=5.0)

        self.assertIsInstance(trade_pnl, TradePnL)
        self.assertEqual(trade_pnl.net_pnl, 15.0)
        self.assertTrue(is_dataclass(trade_pnl))
        self.assertFalse(hasattr(trade_pnl, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            trade_pnl.transaction_cost = 0.0
        with self.assertRaises(ValueError):
            build_trade_pnl(trade, 20.0, transaction_cost=-1.0)
        with self.assertRaises(ValueError):
            build_trade_pnl(trade, 20.0, transaction_cost=5.0, net_pnl=16.0)

    def test_engine_accepts_injected_cost_model_and_rejects_none(self) -> None:
        """Use injected collaborators without runtime protocol inspection."""
        model = FixedRateTransactionCostModel(0.0, 0.0, 0.0, 0.0, 0.0)
        engine = RealizedPnLEngine(model)

        self.assertIs(engine.transaction_cost_model, model)
        self.assertEqual(engine.calculate((_trade(),)).trade_pnls[0].net_pnl, 20.0)
        with self.assertRaises(TypeError):
            RealizedPnLEngine(None)

    def test_calculation_is_deterministic_and_does_not_mutate_trade(self) -> None:
        """Return equal net facts for equal inputs while preserving source identity."""
        trade = _trade()
        engine = RealizedPnLEngine(
            FixedRateTransactionCostModel(0.001, 0.0, 0.0, 0.0, 0.0)
        )

        first = engine.calculate((trade,)).trade_pnls[0]
        second = engine.calculate((trade,)).trade_pnls[0]

        self.assertEqual(first, second)
        self.assertIs(first.source_completed_trade, trade)
        self.assertEqual(trade.entry_price, 100.0)
        self.assertEqual(trade.exit_price, 110.0)


def _trade() -> CompletedTrade:
    """Build one explicit immutable completed trade for net-PnL fixtures."""
    return build_completed_trade(
        _accepted_result(),
        ExecutionSide.LONG,
        2,
        100.0,
        110.0,
    )
