"""Canonical trading-session model."""

from dataclasses import dataclass
from datetime import date

from src.engines.data.models.candle import Candle
from src.engines.data.models.types import Instrument, Timeframe, Weekday


@dataclass(frozen=True, slots=True)
class Session:
    """Represents immutable trading-session context and its candle collection."""

    session_date: date
    instrument: Instrument
    timeframe: Timeframe
    weekday: Weekday
    is_weekly_expiry: bool
    is_monthly_expiry: bool
    has_holiday_gap: bool
    candles: tuple[Candle, ...]
