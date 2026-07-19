"""Stable public architecture surface for the Data Engine."""

from src.engines.data.interfaces import (
    DataAccess,
    DataEngine,
    DataSource,
)
from src.engines.data.validation import (
    CandleValidationResult,
    ValidationCode,
    ValidationIssue,
    ValidationSeverity,
    validate_candle,
    validate_candles,
)
from src.engines.data.models import Candle, Instrument, Session, Timeframe, Weekday
from src.engines.data.exceptions import (
    DataAccessError,
    DataEngineError,
    DataNormalizationError,
    DataSourceError,
    UnsupportedInstrumentError,
    UnsupportedTimeframeError,
)

__all__ = [
    "DataAccess",
    "DataAccessError",
    "DataEngine",
    "DataEngineError",
    "DataNormalizationError",
    "DataSource",
    "DataSourceError",
    "Candle",
    "CandleValidationResult",
    "Instrument",
    "Session",
    "Timeframe",
    "UnsupportedInstrumentError",
    "UnsupportedTimeframeError",
    "Weekday",
    "ValidationCode",
    "ValidationIssue",
    "ValidationSeverity",
    "validate_candle",
    "validate_candles",
]
