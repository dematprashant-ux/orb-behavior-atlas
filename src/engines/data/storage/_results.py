"""Immutable results returned from canonical storage operations."""

from dataclasses import dataclass

from src.engines.data.models import Candle, Session
from src.engines.data.storage._identity import SessionIdentity


@dataclass(frozen=True, slots=True)
class StoreSessionResult:
    """Confirms persistence of one canonical session identity."""

    identity: SessionIdentity


@dataclass(frozen=True, slots=True)
class LoadSessionResult:
    """Represents a found canonical session or an absent identity."""

    session: Session | None


@dataclass(frozen=True, slots=True)
class LoadCandlesResult:
    """Contains canonical candles in ascending canonical timestamp order."""

    candles: tuple[Candle, ...]

    def __post_init__(self) -> None:
        """Prevent backend-native or duplicate timestamp ordering from escaping."""
        previous_timestamp = None
        for candle in self.candles:
            if not isinstance(candle, Candle):
                raise TypeError("candles must contain Candle objects")
            if previous_timestamp is not None and candle.timestamp <= previous_timestamp:
                raise ValueError("candles must be in strictly ascending canonical timestamp order")
            previous_timestamp = candle.timestamp
