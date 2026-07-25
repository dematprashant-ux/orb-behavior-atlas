"""Contract tests for stateless deterministic portfolio capital allocation."""

from dataclasses import FrozenInstanceError, is_dataclass
from unittest import TestCase

from src.engines.portfolio import (
    AllocationDecision,
    AllocationRequest,
    CapitalAllocationPolicy,
    FixedCapitalAllocationPolicy,
    PercentageCapitalAllocationPolicy,
)


class PortfolioAllocationTests(TestCase):
    """Verify allocation remains separate from quantity sizing and lifecycle."""

    def test_fixed_policy_caps_requested_capital_at_available_cash(self) -> None:
        """Allocate fixed capital below, at, and above explicit available cash."""
        policy = FixedCapitalAllocationPolicy(100.0)

        self.assertEqual(policy.allocate(AllocationRequest(250.0)).allocated_capital, 100.0)
        self.assertEqual(policy.allocate(AllocationRequest(100.0)).allocated_capital, 100.0)
        self.assertEqual(policy.allocate(AllocationRequest(50.0)).allocated_capital, 50.0)

    def test_zero_cash_and_zero_percentage_produce_zero_allocation(self) -> None:
        """Represent no requested capital deterministically without rejection state."""
        self.assertEqual(
            FixedCapitalAllocationPolicy(100.0)
            .allocate(AllocationRequest(0.0))
            .allocated_capital,
            0.0,
        )
        self.assertEqual(
            PercentageCapitalAllocationPolicy(0.0)
            .allocate(AllocationRequest(100.0))
            .allocated_capital,
            0.0,
        )

    def test_percentage_policy_uses_available_cash_as_its_explicit_base(self) -> None:
        """Allocate configured decimal fractions without valuation or rounding."""
        policy: CapitalAllocationPolicy = PercentageCapitalAllocationPolicy(0.25)

        self.assertEqual(policy.allocate(AllocationRequest(200.0)).allocated_capital, 50.0)
        self.assertEqual(
            PercentageCapitalAllocationPolicy(1.0)
            .allocate(AllocationRequest(200.0))
            .allocated_capital,
            200.0,
        )

    def test_models_and_policies_are_immutable_and_deterministic(self) -> None:
        """Expose stable value behavior without mutating requests."""
        request = AllocationRequest(100.0)
        policy = FixedCapitalAllocationPolicy(60.0)
        first = policy.allocate(request)
        second = policy.allocate(request)

        self.assertEqual(first, second)
        self.assertIsInstance(first, AllocationDecision)
        self.assertTrue(is_dataclass(request))
        self.assertTrue(is_dataclass(policy))
        self.assertFalse(hasattr(first, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            request.available_cash = 0.0
        with self.assertRaises(FrozenInstanceError):
            policy.capital = 0.0

    def test_allocation_boundary_rejects_intrinsic_misuse(self) -> None:
        """Reject invalid capital facts, percentage values, and request types."""
        with self.assertRaises(ValueError):
            AllocationRequest(-1.0)
        with self.assertRaises(ValueError):
            FixedCapitalAllocationPolicy(-1.0)
        with self.assertRaises(ValueError):
            PercentageCapitalAllocationPolicy(1.1)
        with self.assertRaises(TypeError):
            PercentageCapitalAllocationPolicy(0)
        with self.assertRaises(TypeError):
            FixedCapitalAllocationPolicy(1.0).allocate(object())
        with self.assertRaises(TypeError):
            AllocationDecision(1)
