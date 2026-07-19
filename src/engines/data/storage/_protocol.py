"""Technology-neutral protocol for canonical Data Engine persistence."""

from typing import Protocol

from src.engines.data.storage._requests import (
    LoadCandlesRequest,
    LoadSessionRequest,
    StoreSessionRequest,
)
from src.engines.data.storage._results import (
    LoadCandlesResult,
    LoadSessionResult,
    StoreSessionResult,
)


class DataStore(Protocol):
    """Stores canonical sessions and retrieves canonical sessions or candles."""

    def store_session(self, request: StoreSessionRequest) -> StoreSessionResult:
        """Persist one aggregate or raise a conflict for an existing identity."""

    def load_session(self, request: LoadSessionRequest) -> LoadSessionResult:
        """Return a session preserving its stored canonical candle order."""

    def load_candles(self, request: LoadCandlesRequest) -> LoadCandlesResult:
        """Return candles ordered by ascending canonical timestamp."""
