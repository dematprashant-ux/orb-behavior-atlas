"""Private ordering helpers for session construction."""

from collections.abc import Sequence

from src.engines.data.exceptions import SessionConstructionError
from src.engines.data.models import Candle


def require_strictly_increasing(candles: Sequence[Candle]) -> None:
    """Reject duplicate and descending timestamps without reordering candles."""
    for previous, current in zip(candles, candles[1:]):
        if current.timestamp == previous.timestamp:
            raise SessionConstructionError("Session candles cannot contain duplicate timestamps.")
        if current.timestamp < previous.timestamp:
            raise SessionConstructionError("Session candles must be strictly timestamp-ordered.")
