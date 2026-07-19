"""Private grouping helpers for session construction."""

from collections.abc import Sequence
from datetime import date

from src.engines.data.exceptions import SessionConstructionError
from src.engines.data.models import Candle, Instrument, Timeframe

SessionKey = tuple[date, Instrument, Timeframe]


def session_key(candle: Candle) -> SessionKey:
    """Return the canonical grouping key for one candle."""
    return candle.session_date, candle.instrument, candle.timeframe


def require_homogeneous(candles: Sequence[Candle]) -> SessionKey:
    """Require every candle to have the same canonical session key."""
    expected_key = session_key(candles[0])
    if any(session_key(candle) != expected_key for candle in candles[1:]):
        raise SessionConstructionError(
            "A session can contain candles from only one date, instrument, and timeframe."
        )
    return expected_key


def sorted_session_keys(keys: Sequence[SessionKey]) -> tuple[SessionKey, ...]:
    """Return session keys in deterministic chronological canonical order."""
    return tuple(sorted(keys, key=lambda key: (key[0], key[1].value, key[2].value)))
