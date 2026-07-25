"""Immutable algorithm identity for optimization search strategies."""

from dataclasses import dataclass

__all__ = ["OptimizationStrategyMetadata"]


@dataclass(frozen=True, slots=True)
class OptimizationStrategyMetadata:
    """Identify a search algorithm without exposing its implementation details."""

    name: str

    def __post_init__(self) -> None:
        """Require one stable non-blank algorithm name without normalization."""
        if not isinstance(self.name, str):
            raise TypeError("name must be a str.")
        if not self.name.strip():
            raise ValueError("name must not be blank.")
