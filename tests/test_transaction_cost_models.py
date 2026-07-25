"""Focused contract tests for the pure Backtesting transaction-cost boundary."""

import ast
from dataclasses import FrozenInstanceError, is_dataclass
from math import inf, nan
from unittest import TestCase

from src.engines.backtesting import (
    FixedRateTransactionCostModel,
    TransactionCostBreakdown,
    TransactionCostModel,
    ZeroTransactionCostModel,
)


class TransactionCostModelTests(TestCase):
    """Verify immutable deterministic cost models with no PnL integration."""

    def test_breakdown_preserves_components_and_requires_exact_total(self) -> None:
        """Store finite non-negative costs without rounding or transformation."""
        breakdown = TransactionCostBreakdown(1.0, 2.0, 3.0, 4.0, 5.0, 15.0)

        self.assertEqual(
            breakdown,
            TransactionCostBreakdown(1.0, 2.0, 3.0, 4.0, 5.0, 15.0),
        )
        self.assertTrue(is_dataclass(breakdown))
        self.assertFalse(hasattr(breakdown, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            breakdown.brokerage = 0.0
        with self.assertRaises(ValueError):
            TransactionCostBreakdown(1.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    def test_breakdown_rejects_negative_nonfinite_and_invalid_values(self) -> None:
        """Reject malformed monetary components deterministically."""
        for value in (-1.0, nan, inf):
            with self.subTest(value=value), self.assertRaises(ValueError):
                TransactionCostBreakdown(value, 0.0, 0.0, 0.0, 0.0, 0.0)
        with self.assertRaises(TypeError):
            TransactionCostBreakdown(0, 0.0, 0.0, 0.0, 0.0, 0.0)
        with self.assertRaises(ValueError):
            TransactionCostBreakdown(0.0, 0.0, 0.0, 0.0, 0.0, nan)

    def test_zero_model_returns_explicit_zero_costs_deterministically(self) -> None:
        """Provide a reusable valid no-cost model without mutable state."""
        model = ZeroTransactionCostModel()

        first = model.calculate(entry_price=100.0, exit_price=110.0, quantity=25)
        second = model.calculate(entry_price=100.0, exit_price=110.0, quantity=25)

        self.assertEqual(first, TransactionCostBreakdown(0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
        self.assertEqual(first, second)
        self.assertTrue(is_dataclass(model))
        self.assertFalse(hasattr(model, "__dict__"))

    def test_fixed_rate_model_uses_total_entry_and_exit_turnover(self) -> None:
        """Apply every decimal rate independently over gross two-sided turnover."""
        model = FixedRateTransactionCostModel(0.001, 0.002, 0.003, 0.004, 0.005)

        breakdown = model.calculate(entry_price=100.0, exit_price=120.0, quantity=10)

        total_turnover = (100.0 * 10) + (120.0 * 10)
        self.assertEqual(breakdown.brokerage, total_turnover * 0.001)
        self.assertEqual(breakdown.exchange_fees, total_turnover * 0.002)
        self.assertEqual(breakdown.regulatory_fees, total_turnover * 0.003)
        self.assertEqual(breakdown.taxes, total_turnover * 0.004)
        self.assertEqual(breakdown.slippage, total_turnover * 0.005)
        self.assertEqual(
            breakdown.total_cost,
            sum(
                (
                    total_turnover * 0.001,
                    total_turnover * 0.002,
                    total_turnover * 0.003,
                    total_turnover * 0.004,
                    total_turnover * 0.005,
                ),
                start=0.0,
            ),
        )
        self.assertEqual(
            model.calculate(entry_price=100.0, exit_price=120.0, quantity=10),
            breakdown,
        )

    def test_fixed_rate_model_allows_zero_rates_and_preserves_configuration(self) -> None:
        """Retain all-zero valid rates as an explicit fixed-rate configuration."""
        model = FixedRateTransactionCostModel(0.0, 0.0, 0.0, 0.0, 0.0)

        self.assertEqual(
            model.calculate(entry_price=100.0, exit_price=0.0, quantity=1),
            TransactionCostBreakdown(0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        )
        with self.assertRaises(FrozenInstanceError):
            model.tax_rate = 0.1

    def test_models_reject_invalid_turnover_inputs_and_rates(self) -> None:
        """Reject intrinsic malformed facts without interpreting trade behavior."""
        models = (ZeroTransactionCostModel(), _model())
        invalid_inputs = (
            (0.0, 0.0, 1),
            (-1.0, 0.0, 1),
            (100.0, -1.0, 1),
            (nan, 0.0, 1),
            (100.0, inf, 1),
            (100.0, 0.0, 0),
            (100.0, 0.0, -1),
            (100.0, 0.0, True),
            (100.0, 0.0, inf),
        )
        for model in models:
            for entry_price, exit_price, quantity in invalid_inputs:
                with self.subTest(model=model, quantity=quantity), self.assertRaises(
                    (TypeError, ValueError)
                ):
                    model.calculate(
                        entry_price=entry_price,
                        exit_price=exit_price,
                        quantity=quantity,
                    )
        for rate in (-0.001, nan, inf, 0):
            with self.subTest(rate=rate), self.assertRaises((TypeError, ValueError)):
                FixedRateTransactionCostModel(rate, 0.0, 0.0, 0.0, 0.0)

    def test_public_protocol_accepts_both_pure_models(self) -> None:
        """Exercise both models through the public cost-model protocol."""
        self.assertEqual(_calculate(ZeroTransactionCostModel()).total_cost, 0.0)
        self.assertGreater(_calculate(_model()).total_cost, 0.0)

    def test_cost_module_has_no_execution_or_performance_dependencies(self) -> None:
        """Keep cost calculation independent from integration milestones."""
        with open("src/engines/backtesting/costs.py", encoding="utf-8") as source_file:
            tree = ast.parse(source_file.read())
        imported_modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        self.assertEqual(imported_modules, {"dataclasses", "math"})


def _model() -> FixedRateTransactionCostModel:
    """Build a representative immutable decimal-rate configuration."""
    return FixedRateTransactionCostModel(0.001, 0.001, 0.001, 0.001, 0.001)


def _calculate(model: TransactionCostModel) -> TransactionCostBreakdown:
    """Exercise the public protocol with explicit valid turnover facts."""
    return model.calculate(entry_price=100.0, exit_price=110.0, quantity=1)
