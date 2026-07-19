"""Technology-neutral persistence boundary for canonical Data Engine objects."""

from src.engines.data.storage._identity import CandleIdentity, SessionIdentity
from src.engines.data.storage._protocol import DataStore
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

__all__ = [
    "CandleIdentity",
    "DataStore",
    "LoadCandlesRequest",
    "LoadCandlesResult",
    "LoadSessionRequest",
    "LoadSessionResult",
    "SessionIdentity",
    "StoreSessionRequest",
    "StoreSessionResult",
]
