"""Contract tests for typed walk-forward training and validation boundaries."""

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta
from typing import cast
from unittest import TestCase

from src.engines.backtesting import (
    DatasetWindow,
    DateTimeRange,
    WalkForwardSelection,
    WalkForwardTrainer,
    WalkForwardValidationExecutor,
    WalkForwardValidationResult,
)


class WalkForwardExecutionContractTests(TestCase):
    """Verify structural contracts without executing training or validation."""

    def test_selection_is_immutable_and_has_deterministic_value_semantics(self) -> None:
        selection = WalkForwardSelection("baseline")

        self.assertEqual(selection, WalkForwardSelection("baseline"))
        self.assertEqual(repr(selection), repr(WalkForwardSelection("baseline")))
        with self.assertRaises(FrozenInstanceError):
            selection.selection_id = "changed"  # type: ignore[misc]

    def test_selection_rejects_invalid_identifiers(self) -> None:
        with self.assertRaisesRegex(TypeError, "selection_id"):
            WalkForwardSelection(cast(str, 1))
        with self.assertRaisesRegex(ValueError, "selection_id"):
            WalkForwardSelection("")

    def test_validation_result_is_immutable_and_preserves_references(self) -> None:
        selection = WalkForwardSelection("baseline")
        window = _window()
        result = WalkForwardValidationResult(selection, window)

        self.assertIs(result.selection, selection)
        self.assertIs(result.validation_window, window)
        self.assertEqual(result, WalkForwardValidationResult(selection, window))
        with self.assertRaises(FrozenInstanceError):
            result.selection = WalkForwardSelection("changed")  # type: ignore[misc]

    def test_validation_result_rejects_wrong_intrinsic_types(self) -> None:
        with self.assertRaisesRegex(TypeError, "selection"):
            WalkForwardValidationResult(cast(WalkForwardSelection, "baseline"), _window())
        with self.assertRaisesRegex(TypeError, "validation_window"):
            WalkForwardValidationResult(
                WalkForwardSelection("baseline"),
                cast(DatasetWindow, "window"),
            )

    def test_trainer_protocol_is_structurally_compatible(self) -> None:
        trainer: WalkForwardTrainer = _Trainer()

        self.assertEqual(trainer.train(_window()), WalkForwardSelection("trained"))

    def test_validation_protocol_is_structurally_compatible(self) -> None:
        executor: WalkForwardValidationExecutor = _ValidationExecutor()
        selection = WalkForwardSelection("trained")
        window = _window()

        result = executor.validate(selection, window)

        self.assertIs(result.selection, selection)
        self.assertIs(result.validation_window, window)

    def test_public_exports_include_all_execution_contracts(self) -> None:
        from src.engines.backtesting.walk_forward import (
            WalkForwardSelection as PackageSelection,
        )
        from src.engines.backtesting.walk_forward import (
            WalkForwardTrainer as PackageTrainer,
        )
        from src.engines.backtesting.walk_forward import (
            WalkForwardValidationExecutor as PackageExecutor,
        )
        from src.engines.backtesting.walk_forward import (
            WalkForwardValidationResult as PackageResult,
        )

        self.assertIs(PackageSelection, WalkForwardSelection)
        self.assertIs(PackageTrainer, WalkForwardTrainer)
        self.assertIs(PackageExecutor, WalkForwardValidationExecutor)
        self.assertIs(PackageResult, WalkForwardValidationResult)


class _Trainer:
    """Minimal structural trainer test double."""

    def train(self, training_window: DatasetWindow) -> WalkForwardSelection:
        del training_window
        return WalkForwardSelection("trained")


class _ValidationExecutor:
    """Minimal structural validation-executor test double."""

    def validate(
        self,
        selection: WalkForwardSelection,
        validation_window: DatasetWindow,
    ) -> WalkForwardValidationResult:
        return WalkForwardValidationResult(selection, validation_window)


def _window() -> DatasetWindow:
    """Create one empty typed window without dataset selection behavior."""
    start = datetime(2024, 1, 1, tzinfo=UTC)
    return DatasetWindow(DateTimeRange(start, start + timedelta(minutes=5)), ())
