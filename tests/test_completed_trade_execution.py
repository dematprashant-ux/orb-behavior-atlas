"""Contract tests for explicit immutable completed-trade execution artifacts."""

from dataclasses import FrozenInstanceError, is_dataclass
from math import inf, nan
from unittest import TestCase

from src.engines.execution import (
    CompletedTrade,
    ExecutionSide,
    ExecutionStatus,
    build_completed_trade,
    build_execution_request,
    build_execution_result,
)

from tests.test_execution_foundation import _decision


class CompletedTradeTests(TestCase):
    """Verify closed-trade facts are explicit, immutable, and non-financial."""

    def test_builds_a_long_trade_with_explicit_facts(self) -> None:
        """Retain accepted source, side, quantity, and prices by exact value."""
        source_result = _accepted_result()

        trade = build_completed_trade(
            source_result,
            ExecutionSide.LONG,
            25,
            100.0,
            110.0,
        )

        self.assertIsInstance(trade, CompletedTrade)
        self.assertIs(trade.source_execution_result, source_result)
        self.assertIs(trade.side, ExecutionSide.LONG)
        self.assertEqual(trade.quantity, 25)
        self.assertEqual(trade.entry_price, 100.0)
        self.assertEqual(trade.exit_price, 110.0)

    def test_builds_a_short_trade_without_profitability_inference(self) -> None:
        """Preserve downward price movement without interpreting its PnL meaning."""
        trade = build_completed_trade(
            _accepted_result(),
            ExecutionSide.SHORT,
            10,
            110.0,
            100.0,
        )

        self.assertIs(trade.side, ExecutionSide.SHORT)
        self.assertEqual(trade.entry_price, 110.0)
        self.assertEqual(trade.exit_price, 100.0)

    def test_allows_equal_and_negative_market_movement_prices(self) -> None:
        """Accept price relationships without calculating or validating PnL."""
        equal_price_trade = build_completed_trade(
            _accepted_result(),
            ExecutionSide.LONG,
            1,
            100.0,
            100.0,
        )
        lower_exit_trade = build_completed_trade(
            _accepted_result(),
            ExecutionSide.LONG,
            1,
            100.0,
            90.0,
        )

        self.assertEqual(equal_price_trade.entry_price, equal_price_trade.exit_price)
        self.assertLess(lower_exit_trade.exit_price, lower_exit_trade.entry_price)

    def test_trade_construction_is_deterministic_and_immutable(self) -> None:
        """Return equal frozen trade values while retaining the exact source object."""
        source_result = _accepted_result()
        first = build_completed_trade(
            source_result,
            ExecutionSide.LONG,
            5,
            100.0,
            105.0,
        )
        second = build_completed_trade(
            source_result,
            ExecutionSide.LONG,
            5,
            100.0,
            105.0,
        )

        self.assertEqual(first, second)
        self.assertTrue(is_dataclass(first))
        self.assertFalse(hasattr(first, "__dict__"))
        self.assertIs(first.source_execution_result, source_result)
        with self.assertRaises(FrozenInstanceError):
            first.quantity = 1

    def test_rejected_and_skipped_results_cannot_be_completed_trades(self) -> None:
        """Require an accepted source result without inferring a lifecycle state."""
        for status in (ExecutionStatus.REJECTED, ExecutionStatus.SKIPPED):
            with self.subTest(status=status), self.assertRaisesRegex(ValueError, "ACCEPTED"):
                build_completed_trade(
                    _execution_result(status),
                    ExecutionSide.LONG,
                    1,
                    100.0,
                    110.0,
                )

    def test_builder_rejects_intrinsic_misuse(self) -> None:
        """Require explicit typed side, quantity, and finite price facts."""
        source_result = _accepted_result()

        with self.assertRaises(TypeError):
            build_completed_trade(object(), ExecutionSide.LONG, 1, 100.0, 110.0)
        with self.assertRaises(TypeError):
            build_completed_trade(source_result, "LONG", 1, 100.0, 110.0)
        with self.assertRaises(TypeError):
            build_completed_trade(source_result, ExecutionSide.LONG, True, 100.0, 110.0)
        with self.assertRaises(ValueError):
            build_completed_trade(source_result, ExecutionSide.LONG, 0, 100.0, 110.0)
        with self.assertRaises(ValueError):
            build_completed_trade(source_result, ExecutionSide.LONG, -1, 100.0, 110.0)
        with self.assertRaises(TypeError):
            build_completed_trade(source_result, ExecutionSide.LONG, 1, 100, 110.0)
        with self.assertRaises(ValueError):
            build_completed_trade(source_result, ExecutionSide.LONG, 1, nan, 110.0)
        with self.assertRaises(ValueError):
            build_completed_trade(source_result, ExecutionSide.LONG, 1, 100.0, inf)


def _accepted_result():
    """Build one immutable accepted source result for closed-trade fixtures."""
    return _execution_result(ExecutionStatus.ACCEPTED)


def _execution_result(status: ExecutionStatus):
    """Build one structural execution result without simulating execution."""
    return build_execution_result(build_execution_request(_decision()), status)
