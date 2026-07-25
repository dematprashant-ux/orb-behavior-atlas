"""Contract tests for immutable optimization search-strategy metadata."""

from dataclasses import FrozenInstanceError, is_dataclass
from unittest import TestCase

from src.engines.backtesting import (
    OptimizationStrategyMetadata,
)


class OptimizationStrategyMetadataTests(TestCase):
    """Verify algorithm identity remains separate from execution behavior."""

    def test_metadata_is_immutable_and_has_deterministic_value_semantics(self) -> None:
        first = OptimizationStrategyMetadata("grid")
        second = OptimizationStrategyMetadata("grid")

        self.assertTrue(is_dataclass(first))
        self.assertFalse(hasattr(first, "__dict__"))
        self.assertEqual(first, second)
        self.assertEqual(repr(first), repr(second))
        with self.assertRaises(FrozenInstanceError):
            first.name = "other"  # type: ignore[misc]

    def test_metadata_rejects_invalid_names(self) -> None:
        with self.assertRaisesRegex(TypeError, "name"):
            OptimizationStrategyMetadata(None)  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "blank"):
            OptimizationStrategyMetadata("   ")

    def test_public_export_is_intentional(self) -> None:
        from src.engines.backtesting import OptimizationStrategyMetadata as PackageMeta

        self.assertIs(PackageMeta, OptimizationStrategyMetadata)
