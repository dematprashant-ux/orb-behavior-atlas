"""Exception hierarchy for Data Engine implementations."""

from src.core.exceptions import ORBError


class DataEngineError(ORBError):
    """Base exception for Data Engine failures."""


class DataSourceError(DataEngineError):
    """Raised when a configured data source cannot satisfy a request."""


class DataAccessError(DataEngineError):
    """Raised when Data Engine data cannot be accessed."""


class DataNormalizationError(DataEngineError):
    """Raised when provider-independent values cannot form a canonical candle."""


class UnsupportedInstrumentError(DataEngineError):
    """Raised when a requested instrument is outside the supported universe."""


class UnsupportedTimeframeError(DataEngineError):
    """Raised when a requested timeframe is unsupported."""


__all__ = [
    "DataAccessError",
    "DataEngineError",
    "DataNormalizationError",
    "DataSourceError",
    "UnsupportedInstrumentError",
    "UnsupportedTimeframeError",
]
