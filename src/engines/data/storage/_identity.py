"""Canonical identities owned by the storage boundary."""

from dataclasses import dataclass
from datetime import date, datetime

from src.engines.data.models import Instrument, Timeframe


@dataclass(frozen=True, slots=True)
class CandleIdentity:
    """Uniquely identifies one canonical candle within an instrument timeframe."""

    instrument: Instrument
    timeframe: Timeframe
    timestamp: datetime


@dataclass(frozen=True, slots=True)
class SessionIdentity:
    """Uniquely identifies one canonical trading session."""

    session_date: date
    instrument: Instrument
    timeframe: Timeframe
