"""Pure immutable transaction-cost models for the Backtesting Framework."""

from dataclasses import dataclass
from math import isfinite

__all__ = [
    "FixedRateTransactionCostModel",
    "TransactionCostBreakdown",
    "ZeroTransactionCostModel",
]


@dataclass(frozen=True, slots=True)
class TransactionCostBreakdown:
    """Records absolute transaction costs and their exact component total."""

    brokerage: float
    exchange_fees: float
    regulatory_fees: float
    taxes: float
    slippage: float
    total_cost: float

    def __post_init__(self) -> None:
        """Require finite, non-negative components with a consistent total."""
        components = (
            (self.brokerage, "brokerage"),
            (self.exchange_fees, "exchange_fees"),
            (self.regulatory_fees, "regulatory_fees"),
            (self.taxes, "taxes"),
            (self.slippage, "slippage"),
        )
        for value, field_name in components:
            _validate_non_negative_float(value, field_name)
        _validate_non_negative_float(self.total_cost, "total_cost")
        if self.total_cost != sum((value for value, _ in components), start=0.0):
            raise ValueError("total_cost must equal the sum of all cost components.")


@dataclass(frozen=True, slots=True)
class ZeroTransactionCostModel:
    """Return an explicit all-zero cost breakdown for valid trade facts."""

    def calculate(
        self,
        *,
        entry_price: float,
        exit_price: float,
        quantity: int,
    ) -> TransactionCostBreakdown:
        """Return a zero-cost result after validating explicit turnover inputs."""
        _validate_turnover_inputs(entry_price, exit_price, quantity)
        return TransactionCostBreakdown(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)


@dataclass(frozen=True, slots=True)
class FixedRateTransactionCostModel:
    """Calculate independent decimal-rate costs over total trade turnover."""

    brokerage_rate: float
    exchange_fee_rate: float
    regulatory_fee_rate: float
    tax_rate: float
    slippage_rate: float

    def __post_init__(self) -> None:
        """Require finite, non-negative decimal fractions without rounding."""
        rates = (
            (self.brokerage_rate, "brokerage_rate"),
            (self.exchange_fee_rate, "exchange_fee_rate"),
            (self.regulatory_fee_rate, "regulatory_fee_rate"),
            (self.tax_rate, "tax_rate"),
            (self.slippage_rate, "slippage_rate"),
        )
        for value, field_name in rates:
            _validate_non_negative_float(value, field_name)

    def calculate(
        self,
        *,
        entry_price: float,
        exit_price: float,
        quantity: int,
    ) -> TransactionCostBreakdown:
        """Calculate component costs from entry plus exit turnover exactly."""
        _validate_turnover_inputs(entry_price, exit_price, quantity)
        total_turnover = (entry_price * quantity) + (exit_price * quantity)
        brokerage = total_turnover * self.brokerage_rate
        exchange_fees = total_turnover * self.exchange_fee_rate
        regulatory_fees = total_turnover * self.regulatory_fee_rate
        taxes = total_turnover * self.tax_rate
        slippage = total_turnover * self.slippage_rate
        total_cost = sum(
            (brokerage, exchange_fees, regulatory_fees, taxes, slippage),
            start=0.0,
        )
        return TransactionCostBreakdown(
            brokerage=brokerage,
            exchange_fees=exchange_fees,
            regulatory_fees=regulatory_fees,
            taxes=taxes,
            slippage=slippage,
            total_cost=total_cost,
        )


def _validate_turnover_inputs(
    entry_price: float,
    exit_price: float,
    quantity: int,
) -> None:
    """Require explicit valid turnover facts without inferring trade semantics."""
    _validate_non_negative_float(entry_price, "entry_price")
    if entry_price <= 0:
        raise ValueError("entry_price must be positive.")
    _validate_non_negative_float(exit_price, "exit_price")
    if isinstance(quantity, bool) or not isinstance(quantity, int):
        raise TypeError("quantity must be an int.")
    if quantity <= 0:
        raise ValueError("quantity must be positive.")


def _validate_non_negative_float(value: float, field_name: str) -> None:
    """Require a finite non-negative native float without accepting booleans."""
    if isinstance(value, bool) or not isinstance(value, float):
        raise TypeError(f"{field_name} must be a float.")
    if not isfinite(value):
        raise ValueError(f"{field_name} must be finite.")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative.")
