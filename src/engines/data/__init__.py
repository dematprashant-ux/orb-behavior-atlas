"""Stable public architecture surface for the Data Engine."""

from src.engines.data.interfaces import (
    AccessRecordT,
    DataAccess,
    DataEngine,
    DataSource,
    EngineRecordT,
    QualityReportT,
    SessionT,
    SourceRecordT,
)
from src.engines.data.models import Candle, Instrument, Session, Timeframe, Weekday
from src.engines.data.exceptions import (
    DataAccessError,
    DataEngineError,
    DataSourceError,
    UnsupportedInstrumentError,
    UnsupportedTimeframeError,
)

__all__ = [
    "AccessRecordT",
    "DataAccess",
    "DataAccessError",
    "DataEngine",
    "DataEngineError",
    "DataSource",
    "DataSourceError",
    "EngineRecordT",
    "Candle",
    "Instrument",
    "QualityReportT",
    "Session",
    "SessionT",
    "SourceRecordT",
    "Timeframe",
    "UnsupportedInstrumentError",
    "UnsupportedTimeframeError",
    "Weekday",
]
