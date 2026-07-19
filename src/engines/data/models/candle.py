"""Canonical market-candle model."""

from dataclasses import dataclass
from datetime import date, datetime

from src.engines.data.models.types import Instrument, Timeframe


@dataclass(frozen=True, slots=True)
class Candle:
    """Represents one immutable, provider-neutral OHLCV market observation."""

    instrument: Instrument
    timeframe: Timeframe
    timestamp: datetime
    session_date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
