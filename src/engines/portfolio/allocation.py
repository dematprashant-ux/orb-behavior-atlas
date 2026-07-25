"""Pure deterministic capital-allocation contracts and policies."""

from dataclasses import dataclass
from math import isfinite
from typing import Protocol

__all__ = [
    "AllocationDecision",
    "AllocationRequest",
    "CapitalAllocationPolicy",
    "FixedCapitalAllocationPolicy",
    "PercentageCapitalAllocationPolicy",
]


@dataclass(frozen=True, slots=True)
class AllocationRequest:
    """Requests capital allocation from one explicit available-cash amount."""

    available_cash: float

    def __post_init__(self) -> None:
        """Require finite non-negative available cash without portfolio mutation."""
        _validate_non_negative_float(self.available_cash, "available_cash")


@dataclass(frozen=True, slots=True)
class AllocationDecision:
    """Records one deterministic capital amount without order-size semantics."""

    allocated_capital: float

    def __post_init__(self) -> None:
        """Require finite non-negative allocation without interpreting its use."""
        _validate_non_negative_float(self.allocated_capital, "allocated_capital")


class CapitalAllocationPolicy(Protocol):
    """Defines pure requested-capital allocation without state transitions."""

    def allocate(self, request: AllocationRequest) -> AllocationDecision:
        """Return a deterministic allocation no greater than available cash."""


@dataclass(frozen=True, slots=True)
class FixedCapitalAllocationPolicy:
    """Allocate configured fixed capital, capped deterministically by cash."""

    capital: float

    def __post_init__(self) -> None:
        """Require finite non-negative fixed capital without hidden configuration."""
        _validate_non_negative_float(self.capital, "capital")

    def allocate(self, request: AllocationRequest) -> AllocationDecision:
        """Return fixed capital capped by the request's available cash."""
        _require_request(request)
        return AllocationDecision(min(self.capital, request.available_cash))


@dataclass(frozen=True, slots=True)
class PercentageCapitalAllocationPolicy:
    """Allocate an explicit decimal fraction of available cash.

    Percentage allocation is always based on the request's available cash, not
    on market valuation, total equity, or another implicit capital base.
    """

    percentage: float

    def __post_init__(self) -> None:
        """Require a finite decimal fraction in the inclusive range zero to one."""
        _validate_non_negative_float(self.percentage, "percentage")
        if self.percentage > 1.0:
            raise ValueError("percentage must not exceed 1.0.")

    def allocate(self, request: AllocationRequest) -> AllocationDecision:
        """Return the configured fraction of explicit available cash exactly."""
        _require_request(request)
        return AllocationDecision(request.available_cash * self.percentage)


def _require_request(request: AllocationRequest) -> None:
    """Require the public immutable request model at the allocation boundary."""
    if not isinstance(request, AllocationRequest):
        raise TypeError("request must be an AllocationRequest.")


def _validate_non_negative_float(value: float, field_name: str) -> None:
    """Require a finite non-negative native float without accepting booleans."""
    if isinstance(value, bool) or not isinstance(value, float):
        raise TypeError(f"{field_name} must be a float.")
    if not isfinite(value):
        raise ValueError(f"{field_name} must be finite.")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative.")
