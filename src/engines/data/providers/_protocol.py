"""Typed provider adapter contract compatible with the DataSource boundary."""

from typing import Protocol

from src.engines.data.interfaces import DataSource
from src.engines.data.providers._config import ProviderConfig


class ProviderAdapter(DataSource, Protocol):
    """Defines a configured adapter that returns canonical candles only."""

    @property
    def config(self) -> ProviderConfig:
        """Return immutable declarative configuration for this adapter."""

    def close(self) -> None:
        """Release future provider-owned resources without changing data behavior."""


__all__ = ["ProviderAdapter"]
