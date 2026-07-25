"""Pure selection of canonical candles within explicit half-open time ranges."""

from dataclasses import dataclass
from typing import Protocol

from src.engines.backtesting.walk_forward.models import DateTimeRange
from src.engines.data.models import Candle

__all__ = ["DatasetWindow", "DatasetWindowBuilder", "StandardDatasetWindowBuilder"]


@dataclass(frozen=True, slots=True)
class DatasetWindow:
    """Records one requested range and its selected ordered candle references."""

    requested_range: DateTimeRange
    observations: tuple[Candle, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.requested_range, DateTimeRange):
            raise TypeError("requested_range must be a DateTimeRange.")
        _ordered_candles(self.observations)


class DatasetWindowBuilder(Protocol):
    """Defines deterministic canonical-candle selection by explicit range."""

    def build(
        self,
        observations: tuple[Candle, ...],
        requested_range: DateTimeRange,
    ) -> DatasetWindow:
        """Return selected candles without sorting, transforming, or I/O."""


@dataclass(frozen=True, slots=True)
class StandardDatasetWindowBuilder:
    """Select ordered candles using the canonical ``[start, end)`` contract."""

    def build(
        self,
        observations: tuple[Candle, ...],
        requested_range: DateTimeRange,
    ) -> DatasetWindow:
        """Return existing candle references whose timestamps are in the range."""
        _ordered_candles(observations)
        if not isinstance(requested_range, DateTimeRange):
            raise TypeError("requested_range must be a DateTimeRange.")
        return DatasetWindow(
            requested_range,
            tuple(
                candle
                for candle in observations
                if requested_range.contains(candle.timestamp)
            ),
        )


def _ordered_candles(observations: tuple[Candle, ...]) -> None:
    """Require canonical candle tuples in non-decreasing timestamp order."""
    if not isinstance(observations, tuple):
        raise TypeError("observations must be a tuple of Candle values.")
    if any(not isinstance(candle, Candle) for candle in observations):
        raise TypeError("observations must contain only Candle values.")
    if any(
        current.timestamp < previous.timestamp
        for previous, current in zip(observations, observations[1:])
    ):
        raise ValueError("observations must be in non-decreasing timestamp order.")
