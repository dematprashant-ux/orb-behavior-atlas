"""Explicit immutable identities for completed optimization runs."""

from dataclasses import dataclass

from src.engines.backtesting.optimization import OptimizationRun

__all__ = ["IdentifiedOptimizationRun", "OptimizationRunIdentity"]


@dataclass(frozen=True, slots=True)
class OptimizationRunIdentity:
    """Represent one caller-supplied canonical optimization-run identity."""

    value: str

    def __post_init__(self) -> None:
        """Require a non-blank identity without normalizing its supplied value."""
        if not isinstance(self.value, str):
            raise TypeError("value must be a str.")
        if not self.value.strip():
            raise ValueError("value must not be blank.")


@dataclass(frozen=True, slots=True)
class IdentifiedOptimizationRun:
    """Associate one explicit optimization-run identity with one exact run."""

    identity: OptimizationRunIdentity
    run: OptimizationRun

    def __post_init__(self) -> None:
        """Require complete, typed association inputs without copying either one."""
        if not isinstance(self.identity, OptimizationRunIdentity):
            raise TypeError("identity must be an OptimizationRunIdentity.")
        if not isinstance(self.run, OptimizationRun):
            raise TypeError("run must be an OptimizationRun.")
